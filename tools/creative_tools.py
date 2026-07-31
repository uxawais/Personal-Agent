from tools.registry import register_tool


@register_tool(
    name="enhance_prompt",
    description="Enhance a basic text prompt to make it more detailed, creative, and effective for AI image generation. Adds descriptive language, artistic style references, lighting, mood, and composition details.",
    parameters={
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "The basic prompt to enhance"},
            "style": {
                "type": "string",
                "description": "Artistic style (e.g. realistic, cinematic, anime, oil painting, 3d render, pixel art)",
                "default": "cinematic",
            },
            "detail_level": {
                "type": "string",
                "description": "How much detail to add: brief, moderate, or extensive",
                "default": "moderate",
            },
        },
        "required": ["prompt"],
    },
)
async def enhance_prompt(prompt: str, style: str = "cinematic", detail_level: str = "moderate") -> str:
    detail_instructions = {
        "brief": "Add key visual elements, lighting, and mood.",
        "moderate": "Enrich with composition, color palette, texture, atmosphere, and stylistic references.",
        "extensive": "Fully flesh out every visual aspect: lighting, color theory, composition rules, texture, depth, atmosphere, artistic influences, camera settings, and emotional tone.",
    }

    style_guides = {
        "cinematic": "shot on Arri Alexa, anamorphic lens, dramatic chiaroscuro lighting, rich color grading",
        "realistic": "photorealistic, 8K, hyper-detailed textures, natural lighting, sharp focus",
        "anime": "anime style, cel-shaded, vibrant colors, clean lines, Studio Ghibli inspired",
        "oil painting": "oil on canvas, impasto technique, visible brushstrokes, classical composition",
        "3d": "3D render, octane render, global illumination, ray tracing, highly detailed materials",
        "pixel art": "pixel art, retro game style, limited color palette, crisp pixel edges, 16-bit",
        "watercolor": "watercolor painting, soft washes, paper texture, wet-on-wet technique",
        "sketch": "pencil sketch, cross-hatching, charcoal lines, rough edges, monochrome",
        "fantasy": "fantasy art, magical atmosphere, ethereal lighting, mythical elements, epic scale",
        "cyberpunk": "cyberpunk aesthetic, neon lights, rain-slicked streets, holographic displays, dystopian",
    }

    guide = style_guides.get(style.lower(), style_guides["cinematic"])
    detail = detail_instructions.get(detail_level, detail_instructions["moderate"])

    enhanced = f"""[Enhanced Prompt]
Subject: {prompt}
Style: {style} — {guide}
Detail: {detail}

Masterpiece, best quality, award-winning composition, trending on ArtStation, {guide}, {prompt}, intricate details, professional lighting, stunning visuals, high contrast, balanced composition"""
    return enhanced.strip()


@register_tool(
    name="generate_image_prompt",
    description="Generate a complete, ready-to-use image generation prompt from a simple concept or idea. Creates detailed prompts for Midjourney, DALL-E, Stable Diffusion, or similar AI image generators.",
    parameters={
        "type": "object",
        "properties": {
            "concept": {"type": "string", "description": "The core idea or concept for the image"},
            "format": {
                "type": "string",
                "description": "Output format: midjourney, dalle, stable_diffusion, or general",
                "default": "general",
            },
            "aspect_ratio": {
                "type": "string",
                "description": "Aspect ratio (e.g. 16:9, 1:1, 9:16, 4:3)",
                "default": "16:9",
            },
        },
        "required": ["concept"],
    },
)
async def generate_image_prompt(concept: str, format: str = "general", aspect_ratio: str = "16:9") -> str:
    if format == "midjourney":
        return f"""[Midjourney Prompt]
/imagine prompt: {concept}, cinematic lighting, photorealistic, intricate details, dynamic composition, dramatic atmosphere, volumetric lighting, 8K --ar {aspect_ratio.replace(":", ":")} --v 6 --style raw --s 250"""

    elif format == "dalle":
        return f"""[DALL-E Prompt]
{concept}. Cinematic lighting, photorealistic, highly detailed, balanced composition, vibrant colors, professional photography style."""

    elif format == "stable_diffusion":
        return f"""[Stable Diffusion Prompt]
{concept}, masterpiece, best quality, ultra-detailed, cinematic lighting, sharp focus, intricate details
Negative prompt: low quality, blurry, distorted, ugly, bad anatomy, watermark, text, signature"""

    else:
        return f"""[General AI Image Prompt]
Concept: {concept}
Style: Cinematic, photorealistic, highly detailed
Lighting: Dramatic, volumetric, moody atmosphere
Composition: Rule of thirds, balanced, depth of field
Quality: 8K, masterwork, trending on ArtStation
Aspect Ratio: {aspect_ratio}"""


@register_tool(
    name="suggest_improvements",
    description="Analyze text (a prompt, message, or description) and suggest specific, actionable improvements to make it more effective, creative, or compelling.",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "The text to analyze and improve"},
            "type": {
                "type": "string",
                "description": "Type of text: creative, professional, marketing, or general",
                "default": "general",
            },
        },
        "required": ["text"],
    },
)
async def suggest_improvements(text: str, type: str = "general") -> dict:
    suggestions = {
        "original": text,
        "type": type,
        "suggestions": [
            "Add more specific details and sensory language",
            "Use stronger, more active verbs",
            "Vary sentence structure for better flow",
            "Consider your audience and tailor the tone",
            "Remove filler words and redundancies",
        ],
        "tip": "Be specific. Instead of 'a beautiful scene', describe what makes it beautiful — the colors, textures, lighting, and emotions.",
    }

    if type == "creative":
        suggestions["suggestions"] = [
            "Show, don't tell — use sensory details",
            "Use metaphors and analogies",
            "Create contrast or tension",
            "Vary rhythm and pace",
            "End with a strong, memorable image",
        ]
        suggestions["tip"] = "The most vivid writing engages all five senses, not just sight."

    elif type == "marketing":
        suggestions["suggestions"] = [
            "Lead with the strongest benefit",
            "Create urgency or scarcity",
            "Use social proof where possible",
            "Make your call-to-action crystal clear",
            "Remove jargon — speak your customer's language",
        ]
        suggestions["tip"] = "Great marketing makes the reader feel something. Address their pain point directly."

    elif type == "professional":
        suggestions["suggestions"] = [
            "Open with your main point (inverted pyramid)",
            "Use bullet points for complex info",
            "Be concise — cut words without cutting meaning",
            "Use data and specifics over vague claims",
            "End with a clear next step or ask",
        ]
        suggestions["tip"] = "Professionals value clarity over creativity. Make your point in the first sentence."

    return suggestions


@register_tool(
    name="brainstorm_ideas",
    description="Generate creative ideas, variations, or angles on a given topic. Useful for content creation, marketing campaigns, creative projects, and problem-solving.",
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "The topic or problem to brainstorm ideas for"},
            "count": {"type": "integer", "description": "Number of ideas to generate (1-10)", "default": 5},
        },
        "required": ["topic"],
    },
)
async def brainstorm_ideas(topic: str, count: int = 5) -> dict:
    if count < 1:
        count = 1
    if count > 10:
        count = 10

    angles = [
        f"{i+1}. **The Unexpected Angle** — Approach {topic} from a surprising or counter-intuitive perspective that challenges assumptions.",
        f"{i+2}. **The Hybrid** — Combine {topic} with an unrelated field or concept to create something novel.",
        f"{i+3}. **The Minimalist** — Strip {topic} down to its absolute essence. What's the simplest possible version?",
        f"{i+4}. **The Extreme** — Amplify {topic} to an extreme degree. What does it look like at 10x scale or intensity?",
        f"{i+5}. **The Analogy** — Explain or reimagine {topic} through a powerful analogy from nature, sports, or history.",
        f"{i+6}. **The Time Shift** — How would {topic} be approached in the past (retro) or far future (futuristic)?",
        f"{i+7}. **The Remix** — Mash up {topic} with a current trend or cultural phenomenon.",
        f"{i+8}. **The Constraint** — Add an artificial constraint ({topic} but with a major limitation) to spark creativity.",
        f"{i+9}. **The Opposite** — What's the opposite of {topic}? Explore the inversion.",
        f"{i+10}. **The First Principles** — Break {topic} down to fundamentals and rebuild from scratch.",
    ]

    return {
        "topic": topic,
        "ideas": angles[:count],
        "technique": "Try combining 2-3 of these angles for even more unique results.",
    }