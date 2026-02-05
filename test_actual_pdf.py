import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.pdf_service import PDFAnalysisService

def test():
    service = PDFAnalysisService()
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf", "V3Q12670738.pdf")
    
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        # List files in the pdf directory to help debug
        pdf_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf")
        if os.path.exists(pdf_dir):
            print(f"Contents of {pdf_dir}: {os.listdir(pdf_dir)}")
        return

    print(f"Testing extraction for file: {pdf_path}")
    result = service.analyze_pdf(pdf_path)
    if result["status"] == "error":
        print(f"Error: {result['message']}")
        return

    data = result["data"]
    print("\n" + "="*50)
    print("FINAL EXTRACTED DATA (IST Normalized)")
    print("="*50)
    print(f"PNR/Reference:   {data.get('booking_reference')}")
    print(f"Transport Type:  {data.get('type')}")
    print(f"Carrier Name:    {data.get('carrier')}")
    print(f"Number:          {data.get('flight_number')}")
    print(f"From:            {data.get('from_location')}")
    print(f"To:              {data.get('to_location')}")
    print(f"Travel Date:     {data.get('date')}")
    print(f"Departure Time:  {data.get('departure_time')} (24h)")
    print(f"Arrival Time:    {data.get('arrival_time')} (24h)")
    print(f"Seat Detail:     {data.get('seat_number')}")
    print(f"Total Amount:    ₹{data.get('total_amount')}")
    print("-"*50)
    print("Passenger Information:")
    for i, p in enumerate(data.get('passengers', []), 1):
        print(f"  {i}. {p.get('name')} (Age: {p.get('age')}) - Seat: {p.get('seat')}")
    print("="*50)

if __name__ == "__main__":
    test()
