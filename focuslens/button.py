"""Button widget drawn in the top bar."""

import pygame

from .constants import (
    COL_BTN, COL_BTN_ACTIVE, COL_BTN_HOVER,
    COL_BTN_TEXT, COL_CLOSE, COL_CLOSE_HOVER,
)


class Button:
    def __init__(self, label: str, effect_id: str, width: int) -> None:
        self.label = label
        self.effect_id = effect_id
        self.width = width
        self.rect = pygame.Rect(0, 0, width, 0)
        self.is_active = False

    def update_rect(self, x: int, y: int, h: int) -> None:
        self.rect = pygame.Rect(x, y, self.width, h)

    def draw(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        is_hovered: bool,
    ) -> None:
        if self.effect_id == "close":
            bg = COL_CLOSE_HOVER if is_hovered else COL_CLOSE
        elif self.is_active:
            bg = COL_BTN_ACTIVE
        else:
            bg = COL_BTN_HOVER if is_hovered else COL_BTN

        pygame.draw.rect(surface, bg, self.rect, border_radius=4)
        text = font.render(self.label, True, COL_BTN_TEXT)
        surface.blit(
            text,
            (
                self.rect.centerx - text.get_width() // 2,
                self.rect.centery - text.get_height() // 2,
            ),
        )
