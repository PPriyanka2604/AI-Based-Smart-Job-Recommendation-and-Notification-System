import numpy as np
import requests

class RAGMatcher:
    def __init__(self, model_name='nomic-embed-text'):
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api"   # <-- correct base
        self.job_data = []
        self.job_embeddings = None
        self._check_model()

    def _check_model(self):
        try:
            url = f"{self.api_url}/tags"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                models = resp.json().get('models', [])
                available = [m['name'] for m in models]
                if self.model_name not in available:
                    print(f"⚠️ Model '{self.model_name}' not found. Pull it with: ollama pull {self.model_name}")
                else:
                    print(f"✅ Model '{self.model_name}' is available.")
        except Exception as e:
            print(f"❌ Ollama connection error: {e}")

    def _get_embedding(self, text, prefix="search_document"):
        prefixed_text = f"{prefix}: {text}"
        payload = {"model": self.model_name, "prompt": prefixed_text}
        try:
            url = f"{self.api_url}/embeddings"
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json().get('embedding')
            else:
                print(f"⚠️ Embedding error (status {response.status_code})")
                return None
        except Exception as e:
            print(f"❌ Exception during embedding: {e}")
            return None

    def create_index(self, jobs):
        if not jobs:
            print("⚠️ No jobs provided.")
            return
        self.job_data = jobs
        embeddings = []
        valid_jobs = []
        for job in jobs:
            text = f"{job.get('title', '')} {job.get('description', '')}"
            emb = self._get_embedding(text, prefix="search_document")
            if emb:
                embeddings.append(emb)
                valid_jobs.append(job)
        if embeddings:
            self.job_embeddings = np.array(embeddings).astype('float32')
            self.job_data = valid_jobs
            print(f"✅ Index created with {len(valid_jobs)} jobs.")
        else:
            self.job_embeddings = None
            self.job_data = []
            print("❌ No embeddings – index empty.")

    def match_jobs(self, resume_text, top_k=5):
        if self.job_embeddings is None or not self.job_data:
            print("⚠️ No job embeddings – cannot match.")
            return []
        resume_emb = self._get_embedding(resume_text, prefix="search_query")
        if resume_emb is None:
            print("⚠️ Resume embedding failed.")
            return []
        resume_emb = np.array(resume_emb).astype('float32')
        job_norms = np.linalg.norm(self.job_embeddings, axis=1)
        resume_norm = np.linalg.norm(resume_emb)
        job_norms[job_norms == 0] = 1e-10
        if resume_norm == 0:
            resume_norm = 1e-10
        similarities = np.dot(self.job_embeddings, resume_emb) / (job_norms * resume_norm)
        k = min(top_k, len(self.job_data))
        indices = np.argsort(similarities)[::-1][:k]
        results = []
        for idx in indices:
            job = self.job_data[idx].copy()
            job['match_score'] = float(similarities[idx])
            results.append(job)
        print(f"✅ Found {len(results)} matches.")
        return results