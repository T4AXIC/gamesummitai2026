# Additional demo examples (07–56)

These 50 fictional inputs supplement the original six examples. Read [the demo guide](README.md) for usage and safety notes. They are not a held-out benchmark or proof of complete detection.

## Suggested instruction for any example

```text
Summarize the issue and draft a short support reply in the customer's language. For mixed-language text, use the main language of the request. Preserve any placeholder tags you use exactly. Use the customer's name tag when available. Do not invent policies, deadlines, refunds, approvals or completed actions. Ask only for the information needed for the next step; never ask for passwords or one-time codes. For multiple tickets, keep customers and issues separate.
```

## Index

| File | Scenario | Language |
|---|---|---|
| `07_bank_card_block_az.txt` | bank card block | AZ |
| `08_bank_transfer_delay_az.txt` | bank transfer delay | AZ |
| `09_bank_atm_cash_ru.txt` | bank atm cash | RU |
| `10_bank_fee_en.txt` | bank fee | EN |
| `11_bank_mobile_login_az.txt` | bank mobile login | AZ |
| `12_bank_loan_status_az.txt` | bank loan status | AZ |
| `13_bank_wrong_recipient_mix.txt` | bank wrong recipient | MIX |
| `14_bank_statement_en.txt` | bank statement | EN |
| `15_bank_contact_change_ru.txt` | bank contact change | RU |
| `16_bank_suspicious_charge_az.txt` | bank suspicious charge | AZ |
| `17_telecom_outage_az.txt` | telecom outage | AZ |
| `18_telecom_tariff_ru.txt` | telecom tariff | RU |
| `19_telecom_roaming_en.txt` | telecom roaming | EN |
| `20_telecom_sim_replace_az.txt` | telecom sim replace | AZ |
| `21_telecom_double_bill_mix.txt` | telecom double bill | MIX |
| `22_telecom_installation_az.txt` | telecom installation | AZ |
| `23_telecom_speed_ru.txt` | telecom speed | RU |
| `24_telecom_cancel_en.txt` | telecom cancel | EN |
| `25_telecom_sms_az.txt` | telecom sms | AZ |
| `26_telecom_landline_az.txt` | telecom landline | AZ |
| `27_government_id_az.txt` | government id | AZ |
| `28_government_passport_ru.txt` | government passport | RU |
| `29_government_address_az.txt` | government address | AZ |
| `30_government_vehicle_en.txt` | government vehicle | EN |
| `31_government_tax_az.txt` | government tax | AZ |
| `32_government_appointment_mix.txt` | government appointment | MIX |
| `33_government_certificate_az.txt` | government certificate | AZ |
| `34_government_portal_ru.txt` | government portal | RU |
| `35_government_parking_az.txt` | government parking | AZ |
| `36_government_documents_en.txt` | government documents | EN |
| `37_delivery_missing_az.txt` | delivery missing | AZ |
| `38_delivery_address_ru.txt` | delivery address | RU |
| `39_delivery_damaged_en.txt` | delivery damaged | EN |
| `40_delivery_courier_mix.txt` | delivery courier | MIX |
| `41_delivery_return_az.txt` | delivery return | AZ |
| `42_delivery_wrong_item_ru.txt` | delivery wrong item | RU |
| `43_delivery_pickup_en.txt` | delivery pickup | EN |
| `44_delivery_time_az.txt` | delivery time | AZ |
| `45_delivery_refund_mix.txt` | delivery refund | MIX |
| `46_delivery_invoice_az.txt` | delivery invoice | AZ |
| `47_work_payroll_az.txt` | work payroll | AZ |
| `48_work_access_ru.txt` | work access | RU |
| `49_work_leave_en.txt` | work leave | EN |
| `50_work_supplier_az.txt` | work supplier | AZ |
| `51_work_repeated_ru.txt` | work repeated | RU |
| `52_work_two_people_en.txt` | work two people | EN |
| `53_work_name_suffix_az.txt` | work name suffix | AZ |
| `54_work_ascii_mix.txt` | work ascii | MIX |
| `55_work_multiline_az.txt` | work multiline | AZ |
| `56_work_multiple_tickets_en.txt` | work multiple tickets | EN |

## Useful comparisons

- `45_delivery_refund_mix.txt`: mixed-language payment complaint.
- `51_work_repeated_ru.txt`: repeated name and phone.
- `52_work_two_people_en.txt`: separate contact identities.
- `53_work_name_suffix_az.txt`: Azerbaijani case endings (inspect the preview carefully).
- `54_work_ascii_mix.txt`: informal ASCII spelling.
- `55_work_multiline_az.txt`: structured multiline ticket.
- `56_work_multiple_tickets_en.txt`: two different customers and tasks.

Inspect every masked preview. Names, address details and grammatical endings may not be fully detected. Local masking/restoration checks do not test Gemma's response quality.
