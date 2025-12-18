import os
import logging
from typing import List, Dict, Any


def _format_products_for_prompt(products: List[Dict[str, Any]]) -> str:
    lines = []
    for i, p in enumerate(products, start=1):
        cats = ", ".join(p.get("category", []) or [])
        price = p.get("final_price") or p.get("msrp")
        price_str = f"${price:.2f}" if isinstance(price, (int, float)) else "N/A"
        line = (
            f"{i}. {p.get('name', 'Unknown')} (SKU: {p.get('sku')})\n"
            f"   Category: {cats}\n"
            f"   Price: {price_str}\n"
            f"   URL: {p.get('uri') or 'N/A'}\n"
            f"   Why relevant: {p.get('description') or 'N/A'}\n"
        )
        lines.append(line)
    return "\n".join(lines)


def generate_summary(products: List[Dict[str, Any]], user_query: str) -> str:
    """Generate a natural language summary using OpenAI when available,
    otherwise fall back to a deterministic, template-based response.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    context = _format_products_for_prompt(products)

    if api_key:
        try:
            # Lazy import so environments without openai still run
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            sys_prompt = (
                "You are a helpful shopping assistant. Given a user query and a set of "
                "relevant LG products, write a concise, helpful recommendation. "
                "Be practical, cite specific model names, and end with 1-2 tips."
            )
            user_msg = (
                f"User query: {user_query}\n\n"
                f"Relevant products:\n{context}\n\n"
                f"Instructions: Summarize top picks, mention trade-offs, and suggest next steps."
            )
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.3,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logging.warning("OpenAI call failed, falling back to template summary: %s", e)

    # Fallback deterministic summary
    if not products:
        return (
            "I couldn't find relevant products for your query. Try rephrasing or relaxing "
            "your constraints (e.g., broader category or price range)."
        )

    bullets = []
    for p in products[:3]:
        price = p.get("final_price") or p.get("msrp")
        price_str = f"${price:.2f}" if isinstance(price, (int, float)) else "N/A"
        bullets.append(f"- {p.get('name')} (SKU {p.get('sku')}), around {price_str}")

    return (
        f"For '{user_query}', here are solid options:\n" +
        "\n".join(bullets) +
        "\nTip: Compare panel/size vs. budget, and check stock before ordering."
    )
