import os
import glob
import pandas as pd
from pdf_data import extract_data_from_pdf

def create_extracted_data_file(pdf_data):
    detailed_headers = [
        'Strata Plan', 'Lot', 'Unit Number', 'Levy Entitlement', 'Lot Street Name', 
        'Owner Name', 'Contact Number', 'Notice Address', 'Notice Address Street Address', 
        'Notice Address Suburb', 'Notice Address State', 'Notice Address Postcode', 
        'Levy Address', 'Date of Purchase', 'Date of Entry', 'Owner Email', 
        'Leases', 'Agent Name', 'Tenant Name', 'Tenant Contact', 'Vacant', 
        'Lease Start Date', 'Lease End Date', 'Move In Date', 'Review Date'
    ]
    numeric_headers = [
        0, 1, 2, 3, 4, 5, 6, 7, '7a', '7b', '7c', '7d', 8, 9, 10, 11, 
        12, 13, 14, 15, 16, 17, 18, 19, 20
    ]

    data_rows = []
    for row in pdf_data:
        mapped_row = {header: row.get(header, None) for header in detailed_headers}
        data_rows.append(mapped_row)

    extracted_data_df = pd.DataFrame(data_rows)
    file_path = "New Extracted Data.xlsx"

    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        headers_df = pd.DataFrame([detailed_headers, numeric_headers])
        headers_df.to_excel(writer, header=False, index=False)
        
        extracted_data_df.to_excel(writer, index=False, header=False, startrow=2)

    print(f"New Excel file created with headers and data saved to {file_path}.")

def create_destination_file(pdf_data):
    data_rows = []
    for row in pdf_data:
        destination_data = {
            "S/Plan": row['Strata Plan'],
            "Building Name": None,
            "Lot#": row['Lot'],
            "Unit#": row['Unit Number'],
            "Lot Street No": row['Lot'],
            "Lot Street Name": row['Lot Street Name'],
            "Agent Id": None,
            "Index": None,
            "Name": row['Owner Name'],
            "Salutation": 'Owner',
            "Contact": row['Owner Name'],
            "Phone 1": row['Contact Number'],
            "Phone 2": None,
            "Fax": None,
            "Mobile": row['Contact Number'],
            "Email": row['Owner Email'],
            "Mailing Address 1": row['Notice Address Street Address'],
            "Mailing Address 2": None,
            "Mailing Suburb": row['Notice Address Suburb'],
            "Mailing State": row['Notice Address State'],
            "Mailing Post Code": row['Notice Address Postcode'],
            "Mailing Email": row['Owner Email'],
            "Tenant Name": row['Tenant Name'],
            "Tenant AH": None,
            "Tenant BH": None,
            "Tenant Mobile": row['Tenant Contact'],
            "Tenant Email": None,
            "Tenant Lease Start": row['Lease Start Date'],
            "UOE": None,
            "UOE2": None,
            "Paid to Date": None,
            "Notice Name": None,
            "Notice Address 1": row['Notice Address Street Address'],
            "Notice Address 2": None,
            "Notice Address 3": None,
            "Notice Suburb": row['Notice Address Suburb'],
            "Notice State": row['Notice Address State'],
            "Notice Post Code": row['Notice Address Postcode'],
            "Notice Email": row['Owner Email'],
            "Nominee Name": None,
            "Nominee Address 1": None,
            "Nominee Address 2": None,
            "Nominee Suburb": None,
            "Nominee State": None,
            "Nominee Post Code": None,
            "Nominee Phone 1": None,
            "Nominee Phone 2": None,
            "Nominee Fax": None,
            "Nominee Email": None,
            "Dealing Date": row['Date of Purchase'],
            "Committee Member": None,
            "Weblink": None,
            "Weblink Username": None,
            "Weblink Password": None,
            "Lot Usage": None,
            "Manager": None,
            "CMR": None,
            "BSB": None,
            "ACCOUNT NO": None,
            "ACCOUNT TITLE": None,
            "Arrears": None,
            "Accessory Unit": None,
            "Agent Name": row['Agent Name'],
            "Agent Addr1": row['Notice Address Street Address'] if row['Agent Name'] else None,
            "Agent Addr2": None,
            "Agent Suburb": row['Notice Address Suburb'] if row['Agent Name'] else None,
            "Agent State": row['Notice Address State'] if row['Agent Name'] else None,
            "Agent PCode": row['Notice Address Postcode'] if row['Agent Name'] else None,
            "Agent Phone": None,
            "Agent Fax": None,
            "Agent Email": None,
            "Owner Occupier": None,
            "Levy Recipient": None,
            "Notice Recipient": None,
            "Levy Method": None,
            "Notice Method": None,
            "Corr Method": None
        }
        data_rows.append(destination_data)

    destination_data_df = pd.DataFrame(data_rows)
    file_path = "New Destination Data.xlsx"
    destination_data_df.to_excel(file_path, index=False)
    print(f"New Excel file created data saved to {file_path}.")

def main():
    folder_path = "Data"
    all_pdfs_data = []

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    else:
        pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
        if pdf_files:
            for pdf in pdf_files:
                print(pdf)
                pdf_data = extract_data_from_pdf(pdf)
                all_pdfs_data.extend(pdf_data)
            create_extracted_data_file(all_pdfs_data)
            create_destination_file(all_pdfs_data)
        else:
            print("No PDF files found in the folder.")

if __name__ == '__main__':
    main()
