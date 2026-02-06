from fastapi import APIRouter, Query, Response
from gtts import gTTS
import io

router = APIRouter()

@router.get("/tts")
def get_tts(
    text: str = Query(..., description="Text to speak"),
    lang: str = Query("en", description="Language code (en, tr)")
):
    """
    Generate TTS audio on the fly and stream it back.
    """
    if not text:
        return Response(content=b"", media_type="audio/mpeg")

    # Handle language variants if needed
    tld = 'com'
    if lang == 'en':
        tld = 'com' # US English
    elif lang == 'tr':
        tld = 'com.tr' # Turkish might not need specific TLD but 'com' is fine usually.
                       # gTTS uses Google Translate so 'tr' is standard.

    try:
        tts = gTTS(text=text, lang=lang, tld=tld)
        
        # Save to memory buffer
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        return Response(content=mp3_fp.read(), media_type="audio/mpeg")
    
    except Exception as e:
        print(f"TTS Error: {e}")
        return Response(content=b"", status_code=500)
