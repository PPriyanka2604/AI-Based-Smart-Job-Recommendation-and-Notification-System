import re
import os
from datetime import datetime
from pdfminer.high_level import extract_text
import docx


class ResumeParser:

    # ------------------------------------
    # TEXT EXTRACTION
    # ------------------------------------
    def extract_text_from_pdf(self, file_source):
        return extract_text(file_source)

    def extract_text_from_docx(self, file_source):
        doc = docx.Document(file_source)
        return "\n".join([p.text for p in doc.paragraphs])

    # ------------------------------------
    # DYNAMIC SECTION DETECTION
    # ------------------------------------
    def detect_sections(self, lines):
        """
        Dynamically detect sections based on formatting patterns
        Returns a dictionary of section_name -> (start_line, end_line)
        """
        sections = {}
        current_section = None
        section_start = 0
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                continue
            
            # Check if this line looks like a section header
            is_header = False
            header_name = None
            
            # Pattern 1: Markdown headers (##, #)
            if re.match(r'^#{1,3}\s+', line_stripped):
                is_header = True
                header_name = re.sub(r'^#{1,3}\s+', '', line_stripped).strip()
            
            # Pattern 2: ALL CAPS line (short)
            elif line_stripped.isupper() and len(line_stripped.split()) <= 5:
                is_header = True
                header_name = line_stripped
            
            # Pattern 3: Title Case with colon
            elif re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*:$', line_stripped):
                is_header = True
                header_name = line_stripped[:-1].strip()
            
            if is_header:
                # Save previous section
                if current_section:
                    sections[current_section] = (section_start, i-1)
                
                # Start new section
                current_section = header_name.lower()
                section_start = i
                print(f"  📍 Found header: '{header_name}' at line {i}")
        
        # Save last section
        if current_section:
            sections[current_section] = (section_start, len(lines)-1)
        
        return sections

    # ------------------------------------
    # FIND EXPERIENCE SECTION ONLY
    # ------------------------------------
    def find_experience_section(self, lines):
        """
        Find the EXPERIENCE section specifically
        Returns the lines from the Experience section only
        """
        sections = self.detect_sections(lines)
        
        print("\n  📑 All detected sections:")
        for section_name, (start, end) in sections.items():
            preview = lines[start][:50] + "..." if len(lines[start]) > 50 else lines[start]
            print(f"     - '{section_name}' (lines {start}-{end}): {preview}")
        
        # Look for ANY section that contains 'experience' in the name
        experience_section = None
        for section_name, (start, end) in sections.items():
            section_lower = section_name.lower()
            if 'experience' in section_lower:
                experience_section = (start, end)
                print(f"\n  ✓ Found Experience section: '{section_name}' (lines {start}-{end})")
                break
        
        # If found, return the lines in that section
        if experience_section:
            start, end = experience_section
            return lines[start:end+1]
        
        print("  ⚠ No Experience section found")
        return []

    # ------------------------------------
    # HELPER: Convert text numbers to integers
    # ------------------------------------
    def text_to_number(self, text):
        """Convert textual numbers to integers"""
        text_numbers = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14,
            'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18,
            'nineteen': 19, 'twenty': 20
        }
        return text_numbers.get(text.lower(), 0)

    # ------------------------------------
    # EXTRACT ALL 10 EXPERIENCE PATTERNS
    # ------------------------------------
    def extract_experience_from_text(self, text):
        """Extract ALL 10 experience patterns from text and SUM them"""
        
        total_months = 0
        today = datetime.now()
        
        # Store individual detections for display
        detections = []
        
        print("\n  🔍 Detecting all 10 experience patterns:")
        
        # ============================================
        # PATTERN 1: x years (numeric)
        # ============================================
        pattern1 = r'(\d+)\s*(years?|yrs?)'
        matches = re.finditer(pattern1, text, re.IGNORECASE)
        for match in matches:
            value = int(match.group(1))
            months = value * 12
            total_months += months
            detections.append(f"Pattern 1 (Numeric Years): {value} years = {months} months")
        
        # ============================================
        # PATTERN 2: x.y years (decimal)
        # ============================================
        pattern2 = r'(\d+\.\d+)\s*(years?|yrs?)'
        matches = re.finditer(pattern2, text, re.IGNORECASE)
        for match in matches:
            value = float(match.group(1))
            months = int(value * 12)
            total_months += months
            detections.append(f"Pattern 2 (Decimal Years): {value} years = {months} months")
        
        # ============================================
        # PATTERN 3: Two years (textual)
        # ============================================
        pattern3 = r'(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*(years?|yrs?)'
        matches = re.finditer(pattern3, text, re.IGNORECASE)
        for match in matches:
            text_num = match.group(1).lower()
            value = self.text_to_number(text_num)
            months = value * 12
            total_months += months
            detections.append(f"Pattern 3 (Text Years): {text_num} years = {months} months")
        
        # ============================================
        # PATTERN 4: x months (numeric)
        # ============================================
        pattern4 = r'(\d+)\s*(months?|mons?)'
        matches = re.finditer(pattern4, text, re.IGNORECASE)
        for match in matches:
            months = int(match.group(1))
            total_months += months
            detections.append(f"Pattern 4 (Numeric Months): {months} months")
        
        # ============================================
        # PATTERN 5: Three months (textual)
        # ============================================
        pattern5 = r'(one|two|three|four|five|six|seven|eight|nine|ten)\s*(months?|mons?)'
        matches = re.finditer(pattern5, text, re.IGNORECASE)
        for match in matches:
            text_num = match.group(1).lower()
            value = self.text_to_number(text_num)
            total_months += value
            detections.append(f"Pattern 5 (Text Months): {text_num} months = {value} months")
        
        # ============================================
        # PATTERN 6: Month Year - Month Year
        # ============================================
        pattern6 = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})\s*[-–—to]+\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4}|Present|present|current|Now|now)'
        matches = re.finditer(pattern6, text, re.IGNORECASE)
        for match in matches:
            start_month, start_year, end_month, end_year = match.groups()
            try:
                start_date = datetime.strptime(f"{start_month[:3]} {start_year}", "%b %Y")
                
                if end_year.lower() in ['present', 'current', 'now']:
                    end_date = today
                    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                    total_months += max(months, 1)
                    detections.append(f"Pattern 6 (Month-Present): {start_month} {start_year} - Present = {months} months")
                else:
                    end_date = datetime.strptime(f"{end_month[:3]} {end_year}", "%b %Y")
                    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                    total_months += max(months, 1)
                    detections.append(f"Pattern 6 (Month-Month): {start_month} {start_year} - {end_month} {end_year} = {months} months")
            except:
                pass
        
        # ============================================
        # PATTERN 7: Year - Year
        # ============================================
        pattern7 = r'(\d{4})\s*[-–—to]+\s*(\d{4})'
        matches = re.finditer(pattern7, text)
        for match in matches:
            start_year, end_year = match.groups()
            context = text[max(0, match.start()-30):match.end()+30].lower()
            if 'intern' in context or 'work' in context or 'experience' in context:
                try:
                    start_date = datetime.strptime(f"Jan {start_year}", "%b %Y")
                    end_date = datetime.strptime(f"Jan {end_year}", "%b %Y")
                    months = (end_date.year - start_date.year) * 12
                    total_months += max(months, 12)
                    detections.append(f"Pattern 7 (Year-Year): {start_year} - {end_year} = {months} months")
                except:
                    pass
        
        # ============================================
        # PATTERN 8: Year-Year (last two digits)
        # ============================================
        pattern8 = r'(\d{4})\s*[-–—]+\s*(\d{2})(?!\d)'
        matches = re.finditer(pattern8, text)
        for match in matches:
            start_year, end_year_short = match.groups()
            context = text[max(0, match.start()-30):match.end()+30].lower()
            if 'intern' in context or 'work' in context or 'experience' in context:
                try:
                    end_year = start_year[:2] + end_year_short
                    start_date = datetime.strptime(f"Jan {start_year}", "%b %Y")
                    end_date = datetime.strptime(f"Jan {end_year}", "%b %Y")
                    months = (end_date.year - start_date.year) * 12
                    total_months += max(months, 12)
                    detections.append(f"Pattern 8 (Year-YY): {start_year}-{end_year_short} = {months} months")
                except:
                    pass
        
        # ============================================
        # PATTERN 10: Single year with context
        # ============================================
        pattern10 = r'(?<!\d)(\d{4})(?!\d)'
        matches = re.finditer(pattern10, text)
        for match in matches:
            year = match.group(1)
            context = text[max(0, match.start()-30):match.end()+30].lower()
            
            if ('intern' in context or 'internship' in context or 'work' in context or 'experience' in context):
                surrounding = text[max(0, match.start()-10):match.end()+10]
                if '-' not in surrounding and 'to' not in surrounding and '–' not in surrounding:
                    if year != str(today.year) or 'present' not in context:
                        total_months += 6
                        detections.append(f"Pattern 10 (Single Year): {year} = 6 months")
        
        # Print all detections
        for detection in detections:
            print(f"    ✓ {detection}")
        
        # Print summary
        if len(detections) > 1:
            print(f"\n  📊 Found {len(detections)} experience entries:")
            for i, detection in enumerate(detections, 1):
                print(f"     {i}. {detection}")
            print(f"  🔢 TOTAL: {total_months} months")
        
        return total_months

    # ------------------------------------
    # CALCULATE EXPERIENCE
    # ------------------------------------
    def calculate_experience(self, text):
        """Calculate total experience months from the Experience section only"""
        
        # Split text into lines
        lines = text.split('\n')
        
        # Find ONLY the Experience section
        experience_lines = self.find_experience_section(lines)
        
        if not experience_lines:
            print("  ⚠ No Experience section found")
            return 0
        
        # Join the experience section lines
        experience_text = ' '.join(experience_lines)
        
        print(f"\n📋 Experience section content:")
        for i, line in enumerate(experience_lines[:5]):
            if line.strip():
                print(f"  {i+1}. {line[:100]}")
        
        # Extract ALL patterns from the experience section
        total_months = self.extract_experience_from_text(experience_text)
        
        return total_months

    # ------------------------------------
    # FORMAT EXPERIENCE
    # ------------------------------------
    def format_experience(self, total_months):
        """Convert total months to readable format"""
        
        if total_months == 0:
            return "0 Months", 0, "Entry-Level"
        elif total_months < 12:
            return f"{total_months} Months", round(total_months / 12, 2), "Entry-Level"
        else:
            years = total_months / 12
            if years < 1:
                level = "Entry-Level"
            elif years < 3:
                level = "Junior"
            elif years < 6:
                level = "Mid-Level"
            else:
                level = "Senior"
            
            if years.is_integer():
                return f"{int(years)} Years", years, level
            else:
                years_rounded = round(years, 1)
                return f"{years_rounded} Years", years, level

    # ------------------------------------
    # MAIN PARSER
    # ------------------------------------
    def parse_resume(self, file_source, file_name=None):
        """Main parsing function - ONLY looks at Experience section"""
        
        # Extract text from file
        if file_name:
            ext = os.path.splitext(file_name)[1].lower()
        elif isinstance(file_source, str):
            ext = os.path.splitext(file_source)[1].lower()
        else:
            ext = ""

        if ext == ".pdf":
            text = self.extract_text_from_pdf(file_source)
        elif ext == ".docx":
            text = self.extract_text_from_docx(file_source)
        elif isinstance(file_source, str):
            with open(file_source, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            try:
                text = file_source.read().decode("utf-8", errors="ignore")
            except:
                text = ""

        print("="*70)
        print("🔍 UNIVERSAL EXPERIENCE PARSER - ALL 10 PATTERNS")
        print("="*70)
        
        # Calculate experience ONLY from Experience section
        total_months = self.calculate_experience(text)
        
        # Format the result
        display, years, level = self.format_experience(total_months)
        
        print(f"\n{'='*70}")
        print(f"✅ FINAL RESULT: {display} ({level})")
        print(f"{'='*70}")
        
        return {
            "text": text,
            "experience_display": display,
            "total_experience_years": round(years, 2),
            "total_experience_months": total_months,
            "experience_level": level
        }


if __name__ == "__main__":
    parser = ResumeParser()
    
    # Test with multiple resumes
    print("\n\n" + "="*70)
    print("TESTING: HCL Resume with Multiple Experiences")
    print("="*70)
    
    hcl_resume = """
## PROFESSIONAL EXPERIENCE

- UiPath SDC Core Lead - Automation Club, RGMCT Jun 2025 - Present 
Led automation initiatives on campus, conducting workshops and mentoring peers in RPA.

- AI & ML Virtual Internship - IBM SkillBuild (Virtual) 2025 
Salary Prediction Project - Built a model to classify candidates earning above 50K.
"""
    
    result = parser.parse_resume(hcl_resume, "test.txt")
    
    print("\n\n" + "="*70)
    print("TESTING: Vidhya's Updated Resume with 2 Internships")
    print("="*70)
    
    vidhya_resume = """
## EXPERIENCE

## DevOps Intern - [Internship Studio] (Remote / 2 Months)

- Set up and managed CI/CD pipelines using Jenkins, GitHub, Maven, and Tomcat.

## Cloud Computing Intern – [Codec Technologies] (Remote / 3 Months)

- Gaining hands-on experience using AWS services including EC2, S3, and Lambda.
"""
    
    result2 = parser.parse_resume(vidhya_resume, "test.txt")