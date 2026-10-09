# Copy-and-paste demo texts

These are fictional demo scenarios, not real customer records. Names and identifiers are invented or reused from the project's existing demo fixtures; realistic formats can coincidentally match real values. Never contact the phone numbers or use the identifiers for real transactions. Email addresses use the reserved `example.com` domain.

## Existing examples

Before this folder was added, examples already existed in:

- `app.py`: Bank, Telecom and Government samples loaded by the sector selector.
- `data/handwritten.jsonl`: 20 annotated AZ/RU/EN evaluation cases.
- `README.md`: the masking illustration.

This folder provides convenient plain-text inputs for a live presentation. It is not a new evaluation dataset.

## How to use

1. Start the local app and Gemma server.
2. Select **Custom** in the sector selector and **llamacpp** as the AI provider.
3. Set the model to `gemma-4-E4B` and keep all data types enabled.
4. Copy the entire contents of one `.txt` file into **Customer text**.
5. Paste the corresponding instruction below into **Instruction for the AI**.
6. Inspect the detected values and outgoing masked text, then click **Protect and send**.
7. Expand **Raw model output (still masked)** to compare tags with the restored answer.

Use `01_bank_az.txt` as the main demo and `06_repeated_values_az.txt` to show consistent tags for repeated values. Run your chosen example once before presenting to warm up the model.

## Additional examples

There are **56 plain-text examples** in this folder: the original six below and **50 more numbered 07–56**. See **[EXAMPLES.md](EXAMPLES.md)** for the full additional index and a reusable AI instruction. The extra scenarios cover banking, telecom, government services, delivery and workplace support in Azerbaijani, Russian, English and mixed-language text.

All 56 inputs passed local detected-value leak checks and exact masking/restoration round trips. These checks do not establish complete PII detection or test live model responses.

## Examples and suggested instructions

| File | Scenario | What to look for |
|---|---|---|
| `01_bank_az.txt` | Azerbaijani double-charge complaint | Person, card, FIN, IBAN, phone and email |
| `02_telecom_mixed.txt` | Mixed Azerbaijani/Russian internet complaint | Cyrillic name, phone, FIN and address |
| `03_government_az.txt` | Vehicle inspection request | Patronymic, date, ID card, FIN, address, phone, VÖEN and car plate |
| `04_support_ru.txt` | Russian application-status request | Cyrillic name, passport, date, phone and email |
| `05_payment_en.txt` | English payment complaint | ASCII name, ID card, FIN, card, phone and email |
| `06_repeated_values_az.txt` | Repeated name, card and phone | Repeated values should reuse the same tags |

### 01 — Bank

```text
Bu şikayəti bir cümlə ilə xülasə et və Azərbaycan dilində qısa cavab layihəsi yaz. Araşdırma aparılmadan pulun qaytarılacağına söz vermə. Cavabda müştərinin adını və əlaqə nömrəsini tag şəklində istifadə et. İstifadə etdiyin tagləri olduğu kimi saxla.
```

### 02 — Telecom

```text
Classify this ticket as billing, internet, tariff or other. Set urgency and explain why. Draft a short reply in Russian, addressing the customer by their name tag. Do not invent a restoration deadline or promise compensation. Preserve all tags you use exactly.
```

### 03 — Government

```text
Müraciətin məqsədini xülasə et və Azərbaycan dilində qısa cavab layihəsi yaz. Müraciətçinin adını və avtomobil nömrəsini tag şəklində istifadə et. Rəsmi sənəd siyahısını bilmirsənsə, uydurma; aidiyyəti qurumdan dəqiqləşdirməyi təklif et. İstifadə etdiyin tagləri olduğu kimi saxla.
```

### 04 — Russian support

```text
Кратко опиши запрос и составь вежливый ответ на русском языке, обращаясь к заявителю по тегу имени. Не утверждай, что статус уже проверен. Укажи тег телефона для обратной связи. Сохрани используемые теги без изменений.
```

### 05 — English payment

```text
Summarize the complaint in one sentence and draft a short English acknowledgement addressed to the customer using their name tag. Ask for the transaction reference. Do not promise a refund or say that a review has already happened. Preserve all tags you use exactly.
```

### 06 — Repeated values

```text
Azərbaycan dilində qısa cavab layihəsi yaz. Müştərinin adı, kartı və əlaqə nömrəsi üçün mətndəki tagləri istifadə et. Kartın artıq bərpa edildiyini iddia etmə. İstifadə etdiyin tagləri olduğu kimi saxla.
```

## Limitations

- Masking is deterministic; model wording and tag usage can vary.
- These examples do not establish full protection of arbitrary customer text. Inspect the preview before sending.
- Address and date detection remain known weak points in the broader evaluation. In `03_government_az.txt`, the current preview masks `Sülh küçəsi` but leaves `Sumqayıt` and the house number `12` visible. This is a useful limitation to discuss, not an example of complete address protection.
- Instructions request specific tag usage, but a small model may omit tags. Restoration only replaces tags actually present in its response.
