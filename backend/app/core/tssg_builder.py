"""
TSSG Builder:
Assembles the multimodal Time-Aligned Screen-Speech Graph (TSSG).
Pairs speech segments with active screen tokens and visual diff plateaus.
"""

from typing import List, Optional
from pathlib import Path

from backend.app.schemas.tssg import TSSGGraph, ScreenToken, ASRWord, VisualDiffEvent
from backend.app.schemas.reel_ir import WordAlignment


class TSSGBuilder:
    def __init__(self, video_id: str, duration_seconds: float):
        self.video_id = video_id
        self.duration_seconds = duration_seconds

    def build_graph(
        self,
        screen_tokens: List[ScreenToken],
        asr_words: List[ASRWord],
        diff_events: List[VisualDiffEvent],
        repaired_words: Optional[List[WordAlignment]] = None,
    ) -> TSSGGraph:
        """
        Constructs the immutable TSSGGraph structure.
        """
        graph = TSSGGraph(
            video_id=self.video_id,
            duration_seconds=self.duration_seconds,
            screen_tokens=screen_tokens,
            asr_words=asr_words,
            diff_events=diff_events,
            metadata={
                "total_screen_tokens": len(screen_tokens),
                "total_asr_words": len(asr_words),
                "total_repaired_terms": sum(1 for w in (repaired_words or []) if w.raw_asr_word is not None),
                "plateau_count": sum(1 for d in diff_events if d.is_plateau),
            },
        )
        return graph
