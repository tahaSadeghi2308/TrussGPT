from flask import Blueprint, request, jsonify
import os, json
from openai import OpenAI
from pathlib import Path
from app.config import SECRET_KEY

chat_bp = Blueprint("chat", __name__)

LOGIC_FOLDER = Path(__file__).parent.parent / "logic"
RESULTS_FILE = LOGIC_FOLDER / "truss_results.json"
IMAGE_FILE = LOGIC_FOLDER / "truss_deformation.png"

client = OpenAI(api_key=SECRET_KEY)

@chat_bp.route("/api/chat/req", methods=["POST"])
def api_chat_req():
    """Handle chat request from user with AI integration."""
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"ok": False, "errors": ["Message cannot be empty."]}), 400

    calculation_context = ""
    image_url = None

    if RESULTS_FILE.exists():
        try:
            with open(RESULTS_FILE, "r") as f:
                results = json.load(f)

            calc_summary = ["Truss Calculation Results:\n"]

            calc_summary.append("\nDisplacements:")
            for disp in results.get("displacements", []):
                calc_summary.append(
                    f"  Node {disp['node_id']}: ux = {disp['ux']:.6e} m, uy = {disp['uy']:.6e} m"
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
    if any(keyword in message_lower for keyword in ["image", "picture", "plot", "visualization", "graph", "diagram"]):
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

    system_prompt = (
        "You are a helpful assistant specialized in structural engineering and truss analysis. "
        "You help users understand their truss calculation results, including displacements, "
        "forces, stresses, and failure analysis. Be concise, technical, and helpful."
    )

    user_prompt = message
    if calculation_context:
        user_prompt = f"{calculation_context}\n\nUser question: {message}"

    if not SECRET_KEY:
        response_text = f"I received your message: {message}\n\n"
        if calculation_context:
            response_text += f"\n{calculation_context}\n\n"
        response_text += "Note: AI API key not configured. Please set AI_API_KEY in your environment."
        return jsonify({"ok": True, "response": response_text})

    try:
        ai_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
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