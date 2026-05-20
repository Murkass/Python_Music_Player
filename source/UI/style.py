from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UITheme:
	name: str
	background: tuple[str, str]
	panel: tuple[str, str]
	surface: tuple[str, str]
	elevated: tuple[str, str]
	accent: tuple[str, str]
	accent_hover: tuple[str, str]
	accent_soft: tuple[str, str]
	text: tuple[str, str]
	text_muted: tuple[str, str]
	border: tuple[str, str]
	success: tuple[str, str]
	danger: tuple[str, str]


THEMES: dict[str, UITheme] = {
	"Oceano": UITheme(
		name="Oceano",
		background=("#eef4ff", "#09111f"),
		panel=("#dce8ff", "#0d1728"),
		surface=("#ffffff", "#132033"),
		elevated=("#f7faff", "#1a2940"),
		accent=("#1d4ed8", "#4f8cff"),
		accent_hover=("#1e40af", "#77a5ff"),
		accent_soft=("#cfe0ff", "#233a5d"),
		text=("#10203a", "#eef4ff"),
		text_muted=("#56657f", "#9eb0c8"),
		border=("#c3d4f2", "#24354c"),
		success=("#0f766e", "#34d399"),
		danger=("#b42318", "#ff7d66"),
	),
	"Grafite": UITheme(
		name="Grafite",
		background=("#f2f2f0", "#111315"),
		panel=("#e3e2dd", "#181c1f"),
		surface=("#ffffff", "#20262b"),
		elevated=("#faf9f6", "#262d33"),
		accent=("#111827", "#f59e0b"),
		accent_hover=("#1f2937", "#ffb949"),
		accent_soft=("#ddd6c8", "#3d3425"),
		text=("#161616", "#f7f6f1"),
		text_muted=("#646464", "#b0b4bb"),
		border=("#d4d0c7", "#30363d"),
		success=("#166534", "#4ade80"),
		danger=("#b42318", "#ff8b7a"),
	),
	"Floresta": UITheme(
		name="Floresta",
		background=("#edf7f0", "#09150f"),
		panel=("#d9efdf", "#102018"),
		surface=("#ffffff", "#16261d"),
		elevated=("#f5fbf7", "#1d3026"),
		accent=("#166534", "#37c871"),
		accent_hover=("#14532d", "#58df8d"),
		accent_soft=("#ccead5", "#254431"),
		text=("#143120", "#eef9f2"),
		text_muted=("#5f7667", "#9db5a5"),
		border=("#c5e1cb", "#2d4738"),
		success=("#0f766e", "#34d399"),
		danger=("#b42318", "#ff8b7a"),
	),
	"Terracota": UITheme(
		name="Terracota",
		background=("#fff3eb", "#1b120f"),
		panel=("#ffe1d0", "#261915"),
		surface=("#fffdf9", "#30201c"),
		elevated=("#fff7f2", "#392723"),
		accent=("#c2410c", "#ff8b4d"),
		accent_hover=("#9a3412", "#ffab78"),
		accent_soft=("#ffd9c2", "#4b2d24"),
		text=("#442015", "#fff1ea"),
		text_muted=("#886657", "#c2a596"),
		border=("#f1d0bd", "#51362d"),
		success=("#166534", "#4ade80"),
		danger=("#c1121f", "#ff8b7a"),
	),
}

LEGACY_THEME_MAP = {
	"blue": "Oceano",
	"dark-blue": "Grafite",
	"green": "Floresta",
}


def available_theme_names() -> list[str]:
	return list(THEMES.keys())


def resolve_theme_name(theme_name: str | None) -> str:
	if not theme_name:
		return "Oceano"
	normalized = LEGACY_THEME_MAP.get(theme_name, theme_name)
	return normalized if normalized in THEMES else "Oceano"


def get_theme(theme_name: str | None) -> UITheme:
	return THEMES[resolve_theme_name(theme_name)]


def button_tokens(theme: UITheme, variant: str = "primary") -> dict[str, object]:
	if variant == "secondary":
		return {
			"fg_color": theme.accent_soft,
			"hover_color": theme.border,
			"text_color": theme.text,
			"border_width": 0,
		}
	if variant == "ghost":
		return {
			"fg_color": theme.surface,
			"hover_color": theme.accent_soft,
			"text_color": theme.text,
			"border_width": 1,
			"border_color": theme.border,
		}
	if variant == "danger":
		return {
			"fg_color": theme.danger,
			"hover_color": theme.accent_hover,
			"text_color": ("#ffffff", "#ffffff"),
			"border_width": 0,
		}
	if variant == "selected":
		return {
			"fg_color": theme.accent,
			"hover_color": theme.accent_hover,
			"text_color": ("#ffffff", "#ffffff"),
			"border_width": 0,
		}
	return {
		"fg_color": theme.accent,
		"hover_color": theme.accent_hover,
		"text_color": ("#ffffff", "#ffffff"),
		"border_width": 0,
	}
