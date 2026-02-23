from flask import Blueprint, request, jsonify
import json
from openai import OpenAI
from pathlib import Path

from app.config import SECRET_KEY, BASE_URL

chat_bp = Blueprint("chat", __name__)

LOGIC_FOLDER = Path(__file__).parent.parent / "logic"
RESULTS_FILE = LOGIC_FOLDER / "truss_results.json"
IMAGE_FILE = LOGIC_FOLDER / "truss_deformation.png"

def _looks_persian(text):
    return any("\u0600" <= ch <= "\u06FF" for ch in text)

def _sanitize_history(history):
    """Keep only safe chat roles/content and limit length."""
    if not isinstance(history, list):
        return []
    cleaned = []
    for item in history:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in ("user", "assistant"):
            continue
        if not isinstance(content, str):
            continue
        content = content.strip()
        if not content:
            continue
        cleaned.append({"role": role, "content": content})
    return cleaned[-20:]


@chat_bp.route("/api/chat/req", methods=["POST"])
def api_chat_req():
    """Handle chat request from user with AI integration."""
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    history = _sanitize_history(data.get("history", []))

    if not message:
        return jsonify({"ok": False, "errors": ["Message cannot be empty."]}), 400

    calculation_context = ""
    raw_results = None
    image_url = None

    # collect data for answers
    if RESULTS_FILE.exists():
        try:
            with open(RESULTS_FILE, "r") as f:
                results = json.load(f)
            raw_results = results

            calc_summary = ["Truss Calculation Results:\n"]

            calc_summary.append("\nDisplacements:")
            for disp in results.get("displacements", []):
                calc_summary.append(
                    f"  Node {disp['node_id']}: ux = {disp['ux']:.6e} m, uy = {disp['uy']:.6e} m"
                )

            calc_summary.append("\nElement Properties:")
            for eid, elem_data in results.get("elements", {}).items():
                calc_summary.append(
                    f"  Element {eid}: Area = {elem_data['area']:.6e} m², "
                    f"Length = {elem_data['length']:.4f} m, Material = {elem_data['material']}, "
                    f"E = {elem_data['young_modulus']:.2e} Pa"
                )

            calc_summary.append("\nElement Forces:")
            for eid, force_data in results.get("forces", {}).items():
                calc_summary.append(
                    f"  Element {eid}: {force_data['force']:.2f} N ({force_data['status']})"
                )

            calc_summary.append("\nElement Stress Analysis:")
            for eid, result in results.get("element_results", {}).items():
                calc_summary.append(
                    f"  Element {eid}: Force = {result['force']:.2f} N, "
                    f"Stress = {result['stress']:.2e} Pa, Status = {result['status']}"
                )

            calculation_context = "\n".join(calc_summary)

            if IMAGE_FILE.exists():
                image_url = "/api/truss/image"

        except Exception as e:
            calculation_context = f"Error loading results: {str(e)}"

    message_lower = message.lower()
    image_keywords = [
        "image",
        "picture",
        "plot",
        "visualization",
        "visualisation",
        "graph",
        "diagram",
        "تصویر",
        "عکس",
        "نمودار",
        "گراف",
        "دیاگرام",
        "پلات",
    ]
    if any(keyword in message_lower for keyword in image_keywords) or any(k in message for k in image_keywords):
        if image_url:
            return jsonify({
                "ok": True,
                "response": f"Here is the truss deformation visualization: {image_url}\n"
                            f"You can view it at: {request.host_url.rstrip('/')}{image_url}",
                "image_url": image_url,
            })
        else:
            return jsonify({
                "ok": True,
                "response": "No truss image is available. Please calculate the truss first."
            })

    wants_persian = _looks_persian(message)
    language_rule = (
        "LANGUAGE:\n"
        "- If the user writes in Persian, respond in Persian.\n"
        "- Otherwise respond in English.\n"
    )

    system_prompt = (
        "You are a helpful assistant specialized in structural engineering and truss analysis.\n"
        "CRITICAL RULES:\n"
        "- Answer ONLY using the provided truss calculation JSON data and do not mention your data is from a JSON file\n"
        "- If the data is missing or insufficient, say you cannot answer and tell the user to calculate the truss first.\n"
        "- Do not invent nodes/elements/forces/stresses that are not in the data.\n"
        "- Keep responses concise, technical, and helpful.\n"
        + language_rule
    )

    if not SECRET_KEY:
        response_text = f"I received your message: {message}\n\n"
        if calculation_context:
            response_text += f"\n{calculation_context}\n\n"
        response_text += "Note: AI API key not configured. Please set AI_API_KEY in your environment."
        return jsonify({"ok": True, "response": response_text})

    if raw_results is None:
        if wants_persian:
            return jsonify(
                {
                    "ok": True,
                    "response": (
                        "من هنوز به نتایج محاسبات خرپا دسترسی ندارم، بنابراین نمی‌توانم بر اساس مدل شما پاسخ بدهم.\n"
                        "لطفاً ابتدا در صفحه خرپا محاسبه را انجام دهید (Go to chat) و سپس دوباره سوال بپرسید."
                    ),
                }
            )
        return jsonify(
            {
                "ok": True,
                "response": (
                    "I don't have `truss_results.json` yet, so I can't answer based on your truss.\n"
                    "Please go to the truss page and calculate first (Go to chat), then ask again."
                ),
            }
        )

    try:
        if not BASE_URL:
            return jsonify(
                {
                    "ok": False,
                    "errors": ["BASE_URL is not configured. Please set BASE_URL in your environment."],
                }
            ), 500

        # GAPGPT (OpenAI-compatible) client
        gap_client = OpenAI(base_url=BASE_URL, api_key=SECRET_KEY)

        truss_context = (
            "Truss calculation data (authoritative, use this to answer):\n"
            f"{json.dumps(raw_results, ensure_ascii=False)}"
        )

        ai_response = gap_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "system", "content": truss_context},
                *history,
                {"role": "user", "content": message},
            ],
            temperature=0.2,
            max_tokens=1000,
        )

        ai_message = ai_response.choices[0].message.content or "No response from AI."

        if image_url and any(keyword in message_lower for keyword in ["show", "display", "see", "view"]):
            ai_message += f"\n\nTruss visualization image: {request.host_url.rstrip('/')}{image_url}"

        return jsonify({
            "ok": True,
            "response": ai_message,
            "image_url": image_url if image_url else None,
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "errors": [f"Error calling AI API: {str(e)}"]
        }), 500