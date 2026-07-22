"""Voice-to-text transcription model definition."""

from typing import Optional, Tuple

from app.orchestrator.model_base import BaseModelDefinition


class VoiceToTextModel(BaseModelDefinition):
    """
    Voice-to-text transcription specialized model.

    Handles speech recognition, audio transcription, and voice-based queries.
    This is a test model to demonstrate audio capability.
    """

    @property
    def name(self) -> str:
        """Human-readable name."""
        return "Voice to Text"

    @property
    def model_id(self) -> str:
        """Model identifier for voice-to-text service."""
        return "ollama/whisper"

    @property
    def priority(self) -> int:
        """High priority for voice/audio tasks (specific task)."""
        return 88

    @property
    def description(self) -> str:
        """Description of the model."""
        return "Specialized for speech recognition, audio transcription, and voice-to-text conversion"

    @property
    def enabled(self) -> bool:
        """Disabled by default - enable when voice model is available."""
        return True

    def should_route_to_me(
        self, prompt: str, context: Optional[dict] = None
    ) -> Tuple[bool, float, str]:
        """
        Route to this model for voice-to-text tasks.

        Matches:
        - Speech recognition requests
        - Audio transcription
        - Voice-related queries
        - Accent and pronunciation questions

        Args:
            prompt: User prompt
            context: Optional context

        Returns:
            Tuple of (should_route, confidence, reason)
        """
        prompt_lower = prompt.lower()

        # Voice/audio conversion keywords
        voice_keywords = [
            "transcribe",
            "transcription",
            "voice to text",
            "speech to text",
            "convert speech",
            "convert voice",
            "convert audio",
            "recognize speech",
            "recognize voice",
            "audio to text",
            "voice recognition",
            "speech recognition",
            "transcribe audio",
            "transcribe speech",
            "transcribe voice",
            "what did i say",
            "what did they say",
        ]

        # Audio format keywords (increases confidence)
        audio_keywords = [
            "mp3",
            "wav",
            "audio file",
            "voice file",
            "recording",
            "audio recording",
            "voice recording",
            "sound file",
        ]

        # Check for voice keywords
        has_voice_keyword = any(kw in prompt_lower for kw in voice_keywords)
        has_audio_keyword = any(kw in prompt_lower for kw in audio_keywords)

        # Both voice keyword and audio format: very high confidence
        if has_voice_keyword and has_audio_keyword:
            return (
                True,
                0.95,
                "Voice-to-text request with audio file format specified",
            )

        # Just voice keyword: high confidence
        if has_voice_keyword:
            return (True, 0.90, "Voice-to-text transcription request detected")

        # Audio format mentioned: medium-high confidence
        if has_audio_keyword:
            return (True, 0.70, "Audio file format mentioned, possible transcription request")

        # Check for accent/pronunciation questions (related to speech)
        speech_related_keywords = [
            "pronunciation",
            "how to pronounce",
            "how do you say",
            "accent",
            "phonetic",
        ]
        if any(kw in prompt_lower for kw in speech_related_keywords):
            return (True, 0.60, "Speech-related question, possible transcription need")

        # Not a voice-to-text request
        return (False, 0.0, "Not a voice-to-text request")
