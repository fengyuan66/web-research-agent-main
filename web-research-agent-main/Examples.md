1. Name (E.g., The Sequel)

2. Description (Something that is thorough, like an abstract. Not just any, one-dimensional description. Something that I can take in and understand the restaurant to a high extent), around 100 words

3. Images (imageUrl), just the URL is fine

4. Percise address (E.g., 123 Alphabet Street, Vancouver, BC)

5. Price range (E.g., $20-30 CAD)

6. Menu (This should include 5-10 notable / recommended dishes from the menu, be factual!)

7. Genre (E.g., Italian)

Return ONLY a valid JSON object. No markdown, no code fences, no extra text.

Use this exact schema and exact key names:

{
  "description": string | null,
  "address": string | null,
  "phone": string | null,
  "website": string | null,
  "hours": string | null,
  "price_range": string | null,
  "google_rating": number | null,
  "review_count": number | null
}

Rules:
- Include every key exactly as written.
- If unknown, set value to null.
- Do not add any keys not listed.
- Output exactly one JSON object.