import pdfplumber
import re
from au_address_parser import AbAddressUtility

def bold_non_bold_text(page):
    bold_words = []
    non_bold_segments = []
    current_word = ""
    is_bold = None
    in_between_non_bold = False

    for char in page.chars:
        if 'Bold' in char['fontname']:
            if is_bold is False:
                if current_word:
                    if in_between_non_bold:
                        non_bold_segments.append(current_word.strip())

                current_word = ""
            is_bold = True
            current_word += char['text']
            in_between_non_bold = True
        else:
            if is_bold is True:
                if current_word:
                    bold_words.append(current_word.replace(" ", "").strip())
                current_word = ""
            is_bold = False
            current_word += char['text']

    if current_word:
        if is_bold:
            bold_words.append(current_word.strip())
        else:
            if in_between_non_bold:
                non_bold_segments.append(current_word.strip())

    return bold_words, non_bold_segments

def extract_data_from_pdf(pdf_path):
    pdf_data = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number in range(2, len(pdf.pages)):
            page = pdf.pages[page_number]
            text = page.extract_text()
            owner_keys = ['NameAddressforserviceofnoticesOwnerName', 'Dateofentry', 'OwnerEmail', 'ContactNumber', 'NoticeAddress', 'LevyAddress', 'Dateofpurchase']
            page_data = {
                'Strata Plan': '',
                'Lot': '',
                'Unit Number': '',
                'Levy Entitlement': '',
                'Lot Street Name': '',
                'Owner Name': '',
                'Contact Number': '',
                'Notice Address': '',
                'Date of Entry': '',
                'Levy Address': '',
                'Date of Purchase': '',
                'Owner Email': set(),
                'Notice Address Street Address': '',
                'Notice Address Suburb': '',
                'Notice Address State': '',
                'Notice Address Postcode': '',
                'Agent Name': '',
                'Tenant Name': '',
                'Tenant Contact': '',
                'Vacant': '',
                'Lease Start Date': '',
                'Lease Term': ''
            }

            bold_text, non_bold_text = bold_non_bold_text(page)

            last_line = ""
            page_lines = text.split("\n")
            for page_line in page_lines:
                strata_plan_match = re.search(r"Strata Plan (\d+)", page_line)
                if strata_plan_match:
                    page_data['Strata Plan'] = strata_plan_match.group(1)

                lot_match = re.search(r"Lot:\s(\d+)", page_line)
                if lot_match:
                    page_data['Lot'] = lot_match.group(1)
                
                if "lots:" in last_line:
                    lot_match = re.search(r'-?\d+(\.\d+)?', page_line)
                    if lot_match:
                        page_data['Lot'] = lot_match.group(0)

                unit_number_match = re.search(r"Unit no.:\s(\d+)", page_line)
                if unit_number_match:
                    page_data['Unit Number'] = unit_number_match.group(1)

                levy_entitlement_match = re.search(r"(\d+\s/\s\d{1,3}(?:,\d{3})*(?:\.\d{2}))", page_line)
                if levy_entitlement_match:
                    page_data['Levy Entitlement'] = levy_entitlement_match.group(1)

                lot_street_name_match = re.search(    r"ABN:?(?:\s?\d){11}\s+([a-zA-Z0-9\-.,\s]+(?:NSW|VIC|QLD|SA|WA|TAS|NT|ACT)\s+\d{4})", page_line)
                if lot_street_name_match:
                    page_data['Lot Street Name'] = lot_street_name_match.group(1)

                is_owner_keys = all(element in bold_text for element in owner_keys)

                if is_owner_keys:
                    owner_index = bold_text.index('Owners') + 1
                    owner_content_key = bold_text[owner_index:(owner_index + 7)]
                    owner_content_value = non_bold_text[owner_index:(owner_index + 7)]
                    owner_data = dict(zip(owner_content_key, owner_content_value))

                    page_data['Owner Name'] = owner_data.get('NameAddressforserviceofnoticesOwnerName','')
                    page_data['Contact Number'] = owner_data.get('ContactNumber','')
                    notice_address = owner_data.get('NoticeAddress','')
                    page_data['Notice Address'] = notice_address
                    try:
                        addr = AbAddressUtility(notice_address)
                        parsed_address = addr.parsed_addr
                        city = parsed_address['locality']
                        state = parsed_address['state']
                        postal_code = parsed_address['post']
                        page_data['Notice Address Suburb'] = city
                        page_data['Notice Address State'] = state
                        page_data['Notice Address Postcode']= postal_code
                        pattern = r',\s*' + re.escape(city.lower()) + r'\s+' + re.escape(state.lower()) + r'\s+' + re.escape(postal_code) + r'$'
                        page_data['Notice Address Street Address'] = re.sub(pattern, '', notice_address.lower())
                    except Exception as e:
                        street_pattern = re.compile(
                            r"(?P<street>[\w\s/&'-]+(?:Road|Street|Avenue|Rd|PO BOX|Box|Apartment|C/|P O'Neil|Greenhills Street|Chiswick Avenue|TH\d+))"
                        )
                        city_pattern = re.compile(
                            r"\s*(?P<city>[A-Z][a-z]*|[a-z]+|[A-Z]+)\s*(?P<state>[A-Z]{2,3})?\s*(?P<postcode>\d{4})?\b\Z"
                        )
                        state_pattern = re.compile(
                            r"(?P<state>[A-Z]{2,3})\s*(?P<postcode>\d{4})?\b\Z"
                        )
                        postcode_pattern = re.compile(
                            r"(?P<postcode>\d{4})\Z"
                        )

                        street_match = street_pattern.search(notice_address)
                        if street_match:
                            page_data['Notice Address Street Address'] = street_match.group('street')

                        city_match = city_pattern.search(notice_address)
                        if city_match:
                            page_data['Notice Address Suburb'] = city_match.group('city')

                        state_match = state_pattern.search(notice_address)
                        if state_match:
                            page_data['Notice Address State'] = state_match.group('state')

                        postcode_match = postcode_pattern.search(notice_address)
                        if postcode_match:
                            page_data['Notice Address Postcode'] = postcode_match.group('postcode')
                    
                    page_data['Date of Entry'] = owner_data.get('Dateofentry','')
                    page_data['Levy Address'] = owner_data.get('LevyAddress','')
                    page_data['Date of Purchase'] = owner_data.get('Dateofpurchase','')
                    page_data['Owner Email'].add(owner_data.get('OwnerEmail',''))
                else:
                    owner_name_match = re.search(r"Owner Name\s*(.+)", page_line)
                    if owner_name_match:
                        page_data['Owner Name'] = owner_name_match.group(1)

                    contact_number_match = re.search(r"Contact Number\s*(.+)", page_line)
                    if contact_number_match:
                        page_data['Contact Number'] = contact_number_match.group(1)

                    notice_address_match = re.search(r"Notice Address\s*(.+)", page_line)
                    if notice_address_match:
                        notice_address = notice_address_match.group(1)
                        page_data['Notice Address'] = notice_address
                        try:
                            addr = AbAddressUtility(notice_address)
                            parsed_address = addr.parsed_addr
                            city = parsed_address['locality']
                            state = parsed_address['state']
                            postal_code = parsed_address['post']
                            page_data['Notice Address Suburb'] = city
                            page_data['Notice Address State'] = state
                            page_data['Notice Address Postcode']= postal_code
                            pattern = r',\s*' + re.escape(city.lower()) + r'\s+' + re.escape(state.lower()) + r'\s+' + re.escape(postal_code) + r'$'
                            page_data['Notice Address Street Address'] = re.sub(pattern, '', notice_address.lower())

                        except Exception as e:
                            street_pattern = re.compile(
                                r"(?P<street>[\w\s/&'-]+(?:Road|Street|Avenue|Rd|PO BOX|Box|Apartment|C/|P O'Neil|Greenhills Street|Chiswick Avenue|TH\d+))"
                            )
                            city_pattern = re.compile(
                                r"\s*(?P<city>[A-Z][a-z]*|[a-z]+|[A-Z]+)\s*(?P<state>[A-Z]{2,3})?\s*(?P<postcode>\d{4})?\b\Z"
                            )
                            state_pattern = re.compile(
                                r"(?P<state>[A-Z]{2,3})\s*(?P<postcode>\d{4})?\b\Z"
                            )
                            postcode_pattern = re.compile(
                                r"(?P<postcode>\d{4})\Z"
                            )

                            street_match = street_pattern.search(notice_address)
                            if street_match:
                                page_data['Notice Address Street Address'] = street_match.group('street')

                            city_match = city_pattern.search(notice_address)
                            if city_match:
                                page_data['Notice Address Suburb'] = city_match.group('city')

                            state_match = state_pattern.search(notice_address)
                            if state_match:
                                page_data['Notice Address State'] = state_match.group('state')

                            postcode_match = postcode_pattern.search(notice_address)
                            if postcode_match:
                                page_data['Notice Address Postcode'] = postcode_match.group('postcode')

                    date_of_entry_match = re.search(r"Date of entry (\d{2}/\d{2}/\d{4})", page_line)
                    if date_of_entry_match:
                        page_data['Date of Entry'] = date_of_entry_match.group(1)

                    levy_address_match = re.search(r"Levy Address\s*(.+)", page_line)
                    if levy_address_match:
                        page_data['Levy Address'] = levy_address_match.group(1)

                    date_of_purchase_match = re.search(r"Date of purchase (\d{2}/\d{2}/\d{4})", page_line)
                    if date_of_purchase_match:
                        page_data['Date of Purchase'] = date_of_purchase_match.group(1)

                    owner_email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", page_line)
                    if owner_email_match:
                        page_data['Owner Email'].add(owner_email_match.group(0))

                if 'Leases' in bold_text:
                    leases_index = bold_text.index('Leases') + 1
                    leases_content_key = bold_text[leases_index:]
                    leases_content_value = non_bold_text[-len(leases_content_key):]
                    leases_data = dict(zip(leases_content_key, leases_content_value))

                    page_data['Agent Name'] = leases_data.get('AgentName', '')
                    page_data['Tenant Name'] = leases_data.get('Tenantname', '')
                    page_data['Tenant Contact'] = leases_data.get('TenantContact', '')
                    page_data['Lease Term'] = leases_data.get('LeaseTerm', '')
                    page_data['Vacant'] = leases_data.get('Vacant', '')
                    page_data['Lease Start Date'] = leases_data.get('LeaseStartDate', '')
                    page_data['Lease End Date'] = leases_data.get('LeaseEndDate', '')
                    page_data['Move In Date'] = leases_data.get('MoveinDate', '')
                    page_data['Review Date'] = leases_data.get('ReviewDate', '')
                else:
                    agent_name_match = re.search(r"Agent Name\s*(.+)", page_line)
                    if agent_name_match:
                        page_data['Agent Name'] = agent_name_match.group(1)

                    tenant_name_match = re.search(r"Tenant name\s*(.+)", page_line)
                    if tenant_name_match:
                        page_data['Tenant Name'] = tenant_name_match.group(1)

                    tenant_contact_match = re.search(r"Tenant Contact\s*(.+)", page_line)
                    if tenant_contact_match:
                        page_data['Tenant Contact'] = tenant_contact_match.group(1)

                    vacant_match = re.search(r"Vacant\s*(.+)", page_line)
                    if vacant_match:
                        page_data['Vacant'] = vacant_match.group(1)

                    lease_start_date_match = re.search(r"Lease Start Date\s*(.+)", page_line)
                    if lease_start_date_match:
                        page_data['Lease Start Date'] = lease_start_date_match.group(1)

                    lease_end_date_match = re.search(r"Lease End Date\s*(.+)", page_line)
                    if lease_end_date_match:
                        page_data['Lease End Date'] = lease_end_date_match.group(1)

                    move_in_date_match = re.search(r"Move in Date\s*(.+)", page_line)
                    if move_in_date_match:
                        page_data['Move In Date'] = move_in_date_match.group(1)

                    review_date_match = re.search(r"Review Date\s*(.+)", page_line)
                    if review_date_match:
                        page_data['Review Date'] = review_date_match.group(1)

                last_line = page_line
            
            page_data['Owner Email'] = " & ".join(list(page_data['Owner Email']))
            pdf_data.append(page_data)
            print(f"--- Page {page_number + 1} ---")

    return pdf_data
