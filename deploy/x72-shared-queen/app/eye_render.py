from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .stereo_source import StereoZSourceFrame

EYE_RENDER_SCHEMA = "ANTMUX-X72-EYE-RENDER-v0.1"
EYE_RENDER_STATUS = "CANDIDATE"
EYE_RENDER_AUTHORITY = "OBSERVATION_ONLY"

NATIVE_CHANNELS = (
    "yellow_outer",
    "blue_second",
    "mauve_third",
    "rose_inner",
)


def _clamp01(value: float | int) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError("eye-render controls must be finite")
    return max(0.0, min(1.0, out))


@dataclass(frozen=True)
class EyeLightControls:
    yellow_outer: float = 0.0
    blue_second: float = 0.0
    mauve_third: float = 0.0
    rose_inner: float = 0.0
    red_tint: float = 0.0
    gray_filter: float = 0.0
    white_reflection: float = 0.35
    black_stripes: float = 0.20

    @classmethod
    def from_values(
        cls,
        *,
        yellow_outer: float = 0.0,
        blue_second: float = 0.0,
        mauve_third: float = 0.0,
        rose_inner: float = 0.0,
        red_tint: float = 0.0,
        gray_filter: float = 0.0,
        white_reflection: float = 0.35,
        black_stripes: float = 0.20,
    ) -> "EyeLightControls":
        return cls(
            yellow_outer=_clamp01(yellow_outer),
            blue_second=_clamp01(blue_second),
            mauve_third=_clamp01(mauve_third),
            rose_inner=_clamp01(rose_inner),
            red_tint=_clamp01(red_tint),
            gray_filter=_clamp01(gray_filter),
            white_reflection=_clamp01(white_reflection),
            black_stripes=_clamp01(black_stripes),
        )
    def native_boosts(self) -> dict[str, float]:
        return {
            "yellow_outer": self.yellow_outer,
            "blue_second": self.blue_second,
            "mauve_third": self.mauve_third,
            "rose_inner": self.rose_inner,
        }

    def overlays(self) -> dict[str, float]:
        return {
            "red_tint": self.red_tint,
            "gray_filter": self.gray_filter,
            "white_reflection": self.white_reflection,
            "black_stripes": self.black_stripes,
        }


PRESETS: dict[str, EyeLightControls] = {
    "focus_blue": EyeLightControls.from_values(
        blue_second=1.0, white_reflection=0.55, black_stripes=0.22
    ),
    "protection": EyeLightControls.from_values(
        yellow_outer=1.0, blue_second=0.20, white_reflection=0.48
    ),
    "dreamy": EyeLightControls.from_values(
        mauve_third=0.85, blue_second=0.20, gray_filter=0.18
    ),
    "excited_love": EyeLightControls.from_values(
        rose_inner=0.90, blue_second=0.45, white_reflection=0.62
    ),
    "mouse_alert": EyeLightControls.from_values(
        yellow_outer=1.0,
        blue_second=0.85,
        mauve_third=0.40,
        rose_inner=0.55,
        white_reflection=0.72,
        black_stripes=0.36,
    ),
}


@dataclass(frozen=True)
class EyePairRenderFrame:
    controls: EyeLightControls
    left_calculation_theta: float
    right_calculation_theta: float
    center_filter_alpha: float
    edge_filter_alpha: float
    bilateral_signal: tuple[float, ...]

    @classmethod
    def from_stereo_source(
        cls,
        stereo: StereoZSourceFrame,
        *,
        controls: EyeLightControls,
    ) -> "EyePairRenderFrame":
        if type(stereo) is not StereoZSourceFrame:
            raise TypeError("stereo must be exactly StereoZSourceFrame")
        if not stereo.verify():
            raise ValueError("stereo source frame must verify")

        return cls(
            controls=controls,
            left_calculation_theta=stereo.left_theta,
            right_calculation_theta=stereo.right_theta,
            center_filter_alpha=0.10,
            edge_filter_alpha=0.34,
            bilateral_signal=stereo.bilateral_mean,
        )

    def to_dict(self) -> dict[str, Any]:
        blue = self.controls.blue_second
        yellow = self.controls.yellow_outer
        mauve = self.controls.mauve_third
        rose = self.controls.rose_inner
        return {
            "schema": EYE_RENDER_SCHEMA,
            "status": EYE_RENDER_STATUS,
            "authority": EYE_RENDER_AUTHORITY,
            "mutates_queen": False,
            "physical_claim": False,
            "native_light_rule": "BOOST_ONLY_NEVER_DIM",
            "shared_color_basis": "BILATERAL_MEAN",
            "native_boosts": self.controls.native_boosts(),
            "overlays": self.controls.overlays(),
            "linked_illumination": {
                "blue_second_ring": blue,
                "blue_web_lines": blue,
                "blue_crystals": blue,
                "yellow_outer_ring": yellow,
                "yellow_crystals": yellow,
                "mauve_third_ring": mauve,
                "rose_inner_accent": rose,
            },
            "filter_transparency": {
                "center_alpha": self.center_filter_alpha,
                "edge_alpha": self.edge_filter_alpha,
                "center_is_clearer": self.center_filter_alpha < self.edge_filter_alpha,
            },
            "left_eye": {
                "visible_rotation_rad": 0.0,
                "visible_rotation": "NONE",
                "mirror_x": False,
                "signal_side": "G",
                "calculation_theta": self.left_calculation_theta,
                "calculation_direction": "COUNTERCLOCKWISE",
            },
            "right_eye": {
                "visible_rotation_rad": 0.0,
                "visible_rotation": "NONE",
                "mirror_x": False,
                "signal_side": "D",
                "calculation_theta": self.right_calculation_theta,
                "calculation_direction": "CLOCKWISE",
            },
            "stereo_relation": "OPPOSITE_CALCULATION_DIRECTION_STABLE_RENDER",
            "bilateral_signal": list(self.bilateral_signal),
            "all_native_channels_may_coexist": True,
        }
