Return ONLY one valid JSON object. No markdown, no code fences, no extra text.

Use exactly these keys and no others:
- description
- image_url
- address
- price_range
- menu
- genre
- website
- hours

Rules:
- Include every key exactly as written.
- If unknown, try again.
- Do not use placeholders like "available", "n/a", or "unknown".
- For image_url and website: value must be a full URL starting with http:// or https://, otherwise null.
- description: around 100 words, factual.
- menu: array of 5 to 10 dish names (strings), factual. If unavailable, null.
- address: precise street address if available.
- price_range: concise string like "$20-30 CAD".
- genre: cuisine/category string.

Required output shape:

{
  "description": null,
  "image_url": null,
  "address": null,
  "price_range": null,
  "menu": null,
  "genre": null,
  "website": null,
  "hours": null
}