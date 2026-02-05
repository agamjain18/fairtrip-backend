import re
import os
import pdfplumber
from typing import Dict, Any, List, Optional

class PDFAnalysisService:
    """
    Service for analyzing PDFs without AI using deterministic rules and regex.
    Based on production-grade non-AI pipeline.
    """

    @staticmethod
    def is_scanned_pdf(file_path: str) -> bool:
        """
        Detects if a PDF is scanned (image-only) or digital (text layer exists).
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    if page.extract_text():
                        return False
            return True
        except Exception:
            return True

    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extracts all text from a digital PDF.
        """
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Error extracting text: {e}")
        return text

    @staticmethod
    def extract_tables(file_path: str) -> List[List[List[Optional[str]]]]:
        """
        Extracts tables from the PDF.
        """
        tables = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.append(page_tables)
        except Exception as e:
            print(f"Error extracting tables: {e}")
        return tables

    @staticmethod
    def parse_booking_details(text: str) -> Dict[str, Any]:
        """
        Rule-based value extraction for travel bookings.
        """
        data = {
            "booking_reference": None,
            "date": None,
            "total_amount": None,
            "from_location": None,
            "to_location": None,
            "carrier": None,
            "flight_number": None,
            "seat_number": None,
            "departure_time": None,
            "arrival_time": None,
            "type": "unknown",
            "passengers": []
        }

        # Regex Patterns
        patterns = {
            "booking_reference": [
                r"PNR[\s*]*(\d{10})", # IRCTC PNR is usually 10 digits
                r"Booking\s*(?:Ref|Reference|ID|Number)[:\s]*([A-Z0-9]{6,15})",
                r"Confirmation[:\s]*([A-Z0-9]{6,15})",
                r"Reservation[:\s]*([A-Z0-9]{6,15})",
                r"Ticket\s*Number[:\s]*([A-Z0-9-]+)"
            ],
            "date": [
                r"Start\s*Date\W*([\d]+-[A-Za-z]+-\d{4})", # Match "15-Feb-2026"
                r"Date\s*of\s*Journey[:\s]+([\d/-]+|[A-Za-z\s\d,]+)",
                r"Travel\s*Date[:\s]+([\d/-]+)",
                r"Date[:\s]+([\d/-]+)",
                r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
                r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})"
            ],
            "total_amount": [
                r"Total\s*Fare[:\s]*[^\d]*([\d,.]+)",
                r"Total\s*Amount[:\s]*([\d,.]+)",
                r"Total[:\s]*[\$€£]?\s*([\d,.]+)",
                r"Amount\s*Paid[:\s]*([\d,.]+)"
            ],
            "from_location": [
                r"Booked\s*From\s*([A-Za-z\s\(\)]+?)(?=\n|Boarding|To|$)",
                r"Boarding\s*At\s*([A-Za-z\s\(\)]+?)(?=\n|$)",
                r"Origin[:\s]*([A-Z0-9\s,/\(\)-]{3,50})",
                r"From[:\s]*([A-Z0-9\s,/\(\)-]{3,50})"
            ],
            "to_location": [
                r"To\s*\n\s*([A-Za-z\s\(\)]+?)(?=\n|Arrival|$)",
                r"Destination[:\s]*([A-Z0-9\s,/\(\)-]{3,50})",
                r"Arrival(?:\s*To)?[:\s]*([A-Z0-9\s,/\(\)-]{3,50})",
                r"Reservation\s*Upto[:\s]*([A-Z0-9\s,/\(\)-]{3,50})"
            ],
            "carrier": [
                r"Train\s*Name[:\s]*([A-Za-z\s]+)",
                r"Airline(?:\s*Name)?[:\s]*([A-Za-z\s]+)",
                r"Carrier[:\s]*([A-Za-z\s]+)",
                r"Operator[:\s]*([A-Za-z\s]+)"
            ],
            "flight_number": [
                r"Train\s*No\.?/Name\s+(\d{5})",
                r"(\d{5})/[A-Za-z\s]+", # Match "19316/Virbhumi Exp"
                r"(?:Flight|Train|Bus|Vehicle)(?:\s*No|Number)?[:\s]*([A-Z0-9\s-]+)",
                r"\b([A-Z]{2,3})\s*(\d{3,4})\b"
            ],
            "seat_number": [
                r"Seat\s*(?:No|Number)?[:\s]*([A-Z0-9\s/]+)",
                r"Berth\s*(?:No|Number)?[:\s]*([A-Z0-9\s/]+)",
                r"Coach\s*[:\s]*[A-Z0-9]+\s*(?:Seat|Berth)\s*[/\s]*([A-Z0-9]+)"
            ],
            "departure_time": [
                r"Departure\W*(\d{1,2}:\d{2})", # Match "Departure* 20:20"
                r"Departure\s*Time[:\s]*(\d{1,2}:\d{2}(?:\s*[APM]{2})?)",
                r"Dep\.?\s*Time[:\s]*(\d{1,2}:\d{2})",
                r"Starts[:\s]*(\d{1,2}:\d{2})"
            ],
            "arrival_time": [
                r"Arrival\W*(\d{1,2}:\d{2})", # Match "Arrival* 07:00"
                r"Arrival\s*Time[:\s]*(\d{1,2}:\d{2}(?:\s*[APM]{2})?)",
                r"Arr\.?\s*Time[:\s]*(\d{1,2}:\d{2})",
                r"Ends[:\s]*(\d{1,2}:\d{2})"
            ]
        }

        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
                if match:
                    data[key] = match.group(1).strip()
                    break

        # Detect Type
        # If we see IRCTC or Train/Rail, it's a train
        if re.search(r"IRCTC|139|Railway|resv\s*slip|redRail", text, re.IGNORECASE):
            data["type"] = "train"
        elif re.search(r"flight|airline|airways", text, re.IGNORECASE):
            data["type"] = "flight"
        elif re.search(r"hotel|stay|accommodation|resort", text, re.IGNORECASE):
            data["type"] = "hotel"
        elif re.search(r"bus|coach", text, re.IGNORECASE):
            data["type"] = "bus"

        # --- Passenger Detail Extraction ---
        lines = text.split('\n')
        passenger_section = False
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Start of passenger section detection
            if re.search(r"Passenger\s*Details|Traveller\s*Details|Booking\s*Status", line, re.IGNORECASE):
                passenger_section = True
                continue
            
            # 1. Regex for redRail/IRCTC style: "# Name Age Gender Food Choice Booking Status Current Status"
            # Line: "1 Atul Jain 22 M No Food RLWL/3/LB RLWL/3/LB"
            # Pattern: Index Name Age Gender (everything else is status/seat)
            p_match = re.search(r"^(\d+)\s+([A-Za-z\s]+?)\s+(\d{1,2})\s+([MF])\s+(?:No Food|Veg|Non-Veg)?\s*([A-Z0-9/]+)", line, re.IGNORECASE)
            if p_match:
                data["passengers"].append({
                    "name": p_match.group(2).strip(),
                    "age": int(p_match.group(3)),
                    "seat": p_match.group(5).strip() # Using status as seat if proper seat not found
                })
                if not data["seat_number"]:
                    data["seat_number"] = p_match.group(5).strip()
                continue
            
            # 2. Regex for "Name: John, Age: 30..."
            p_alt = re.search(r"Name[:\s]*([A-Za-z\s]+).*Age[:\s]*(\d+).*Seat[:\s]*([A-Z0-9-]+)", line, re.IGNORECASE)
            if p_alt:
                data["passengers"].append({
                    "name": p_alt.group(1).strip(),
                    "age": int(p_alt.group(2)),
                    "seat": p_alt.group(3).strip()
                })
                continue
            
            # 3. Simple CSV/Table fallback for passengers
            # If we are in passenger section, try more relaxed matching
            if passenger_section:
                # Look for name and seat on the same line
                # "John Doe   12A"
                relaxed_match = re.search(r"^([A-Za-z\s]+?)\s{2,}([A-Z0-9]{2,5})\b", line)
                if relaxed_match:
                    name = relaxed_match.group(1).strip()
                    seat = relaxed_match.group(2).strip()
                    # Basic check to avoid false positives (e.g., location names)
                    if len(name) > 3 and not any(kw in name.lower() for kw in ['station', 'airport', 'terminal']):
                        data["passengers"].append({
                            "name": name,
                            "seat": seat,
                            "age": None
                        })

        return data

    @staticmethod
    def validate_data(data: Dict[str, Any]) -> bool:
        """
        Validation layer to reach high accuracy by rejecting invalid outputs.
        """
        # Minimum validation: must have at least a booking reference or a date
        if not data.get("booking_reference") and not data.get("date"):
            return False
            
        # Example strict rules
        if data.get("booking_reference") and len(data["booking_reference"]) < 3:
            return False
            
        if data.get("total_amount"):
            try:
                val = float(data["total_amount"].replace(",", ""))
                if val < 0: return False
            except:
                pass
                
        return True

    def analyze_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Main pipeline entry point.
        """
        if self.is_scanned_pdf(file_path):
            return {
                "status": "error",
                "message": "Scanned PDF detected. Non-AI extraction requires digital PDF with text layer."
            }

        text = self.extract_text(file_path)
        if not text:
            return {
                "status": "error",
                "message": "No text could be extracted from the PDF."
            }

        extracted_data = self.parse_booking_details(text)
        
        # Also try table extraction if data is missing
        if not extracted_data["booking_reference"]:
            tables = self.extract_tables(file_path)
            # Simple table processing logic could go here if needed
        
        is_valid = self.validate_data(extracted_data)
        
        return {
            "status": "success" if is_valid else "partial_success",
            "data": extracted_data,
            "is_valid": is_valid,
            "method": "rule_based_deterministic"
        }
