import pygame
import numpy as np
import sys
from typing import Tuple, Optional

# Constants
ROWS = 6
COLS = 7
SQUARESIZE = 100
RADIUS = int(SQUARESIZE/2 - 5)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
LIGHT_BLUE = (100, 149, 237)
BOARD_COLOR = (0, 0, 139)
BACKGROUND_COLOR = (25, 25, 112)

# Game states
MENU = 0
PLAYING = 1
GAME_OVER = 2

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = pygame.font.SysFont("Arial", 40, bold=True)

    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        # Draw button shadow
        shadow_rect = self.rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        pygame.draw.rect(screen, (0, 0, 0, 128), shadow_rect, border_radius=10)
        
        # Draw main button
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=10)
        
        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

class ConnectFour:
    def __init__(self):
        self.board = np.zeros((ROWS, COLS))
        self.game_over = False
        self.turn = 0  # 0 for player, 1 for AI
        self.winner = None  # Add winner tracking
        
    def drop_piece(self, col: int) -> bool:
        """Drop a piece in the specified column. Returns True if successful."""
        if self.is_valid_location(col):
            row = self.get_next_open_row(col)
            self.board[row][col] = self.turn + 1
            # Check for win after dropping piece
            if self.winning_move(self.turn + 1):
                self.game_over = True
                self.winner = self.turn + 1
            # Check for tie
            elif len(self.get_valid_locations()) == 0:
                self.game_over = True
                self.winner = 0  # 0 represents a tie
            return True
        return False
    
    def is_valid_location(self, col: int) -> bool:
        """Check if the column is valid for dropping a piece."""
        return self.board[0][col] == 0
    
    def get_next_open_row(self, col: int) -> int:
        """Get the next open row in the specified column."""
        for r in range(ROWS-1, -1, -1):
            if self.board[r][col] == 0:
                return r
        return -1
    
    def winning_move(self, piece: int) -> bool:
        """Check if the last move was a winning move."""
        # Check horizontal locations
        for c in range(COLS-3):
            for r in range(ROWS):
                if (self.board[r][c] == piece and 
                    self.board[r][c+1] == piece and 
                    self.board[r][c+2] == piece and 
                    self.board[r][c+3] == piece):
                    return True

        # Check vertical locations
        for c in range(COLS):
            for r in range(ROWS-3):
                if (self.board[r][c] == piece and 
                    self.board[r+1][c] == piece and 
                    self.board[r+2][c] == piece and 
                    self.board[r+3][c] == piece):
                    return True

        # Check positively sloped diagonals
        for c in range(COLS-3):
            for r in range(ROWS-3):
                if (self.board[r][c] == piece and 
                    self.board[r+1][c+1] == piece and 
                    self.board[r+2][c+2] == piece and 
                    self.board[r+3][c+3] == piece):
                    return True

        # Check negatively sloped diagonals
        for c in range(COLS-3):
            for r in range(3, ROWS):
                if (self.board[r][c] == piece and 
                    self.board[r-1][c+1] == piece and 
                    self.board[r-2][c+2] == piece and 
                    self.board[r-3][c+3] == piece):
                    return True
        return False

    def evaluate_window(self, window: np.ndarray, piece: int) -> int:
        """Evaluate a window of 4 pieces."""
        score = 0
        opp_piece = 2 if piece == 1 else 1

        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(0) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(0) == 2:
            score += 2

        if window.count(opp_piece) == 3 and window.count(0) == 1:
            score -= 4

        return score

    def score_position(self, piece: int) -> int:
        """Score the current board position."""
        score = 0

        # Score center column
        center_array = [int(i) for i in list(self.board[:, COLS//2])]
        center_count = center_array.count(piece)
        score += center_count * 3

        # Score horizontal
        for r in range(ROWS):
            row_array = [int(i) for i in list(self.board[r,:])]
            for c in range(COLS-3):
                window = row_array[c:c+4]
                score += self.evaluate_window(window, piece)

        # Score vertical
        for c in range(COLS):
            col_array = [int(i) for i in list(self.board[:,c])]
            for r in range(ROWS-3):
                window = col_array[r:r+4]
                score += self.evaluate_window(window, piece)

        # Score positive sloped diagonal
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = [self.board[r+i][c+i] for i in range(4)]
                score += self.evaluate_window(window, piece)

        # Score negative sloped diagonal
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = [self.board[r+3-i][c+i] for i in range(4)]
                score += self.evaluate_window(window, piece)

        return score

    def is_terminal_node(self) -> bool:
        """Check if the current board state is a terminal node."""
        return (self.winning_move(1) or 
                self.winning_move(2) or 
                len(self.get_valid_locations()) == 0)

    def get_valid_locations(self) -> list:
        """Get list of valid column locations."""
        valid_locations = []
        for col in range(COLS):
            if self.is_valid_location(col):
                valid_locations.append(col)
        return valid_locations

    def minimax(self, depth: int, alpha: float, beta: float, maximizing_player: bool) -> Tuple[Optional[int], int]:
        """Minimax algorithm with alpha-beta pruning."""
        valid_locations = self.get_valid_locations()
        is_terminal = self.is_terminal_node()
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if self.winning_move(2):  # AI wins
                    return (None, 100000000000000)
                elif self.winning_move(1):  # Player wins
                    return (None, -10000000000000)
                else:  # Game is over, no more valid moves
                    return (None, 0)
            else:  # Depth is zero
                return (None, self.score_position(2))

        if maximizing_player:
            value = float('-inf')
            column = valid_locations[0]
            for col in valid_locations:
                row = self.get_next_open_row(col)
                self.board[row][col] = 2
                new_score = self.minimax(depth-1, alpha, beta, False)[1]
                self.board[row][col] = 0
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value

        else:  # Minimizing player
            value = float('inf')
            column = valid_locations[0]
            for col in valid_locations:
                row = self.get_next_open_row(col)
                self.board[row][col] = 1
                new_score = self.minimax(depth-1, alpha, beta, True)[1]
                self.board[row][col] = 0
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

class Game:
    def __init__(self):
        pygame.init()
        self.width = COLS * SQUARESIZE
        self.height = (ROWS + 1) * SQUARESIZE
        self.size = (self.width, self.height)
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption("Connect Four")
        self.font = pygame.font.SysFont("Arial", 75, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 40, bold=True)
        self.game = ConnectFour()
        self.state = MENU
        
        # Create buttons
        button_width = 200
        button_height = 60
        center_x = self.width // 2 - button_width // 2
        
        # Menu button
        self.play_button = Button(center_x, 300, button_width, button_height, 
                                "Play", BLUE, LIGHT_BLUE)
        
        # Game over button
        self.restart_button = Button(center_x, 300, button_width, button_height, 
                                   "Play Again", BLUE, LIGHT_BLUE)

    def draw_menu(self):
        self.screen.fill(BACKGROUND_COLOR)
        
        # Draw title with shadow
        title = self.font.render("Connect Four", True, BLACK)
        title_shadow = self.font.render("Connect Four", True, WHITE)
        title_rect = title.get_rect(center=(self.width//2 + 4, 104))
        title_shadow_rect = title_shadow.get_rect(center=(self.width//2, 100))
        self.screen.blit(title, title_rect)
        self.screen.blit(title_shadow, title_shadow_rect)
        
        # Draw decorative circles
        for i in range(3):
            pygame.draw.circle(self.screen, RED, (100 + i*200, 200), 30)
            pygame.draw.circle(self.screen, YELLOW, (200 + i*200, 200), 30)
        
        self.play_button.draw(self.screen)
        pygame.display.update()

    def draw_game_over(self, winner):
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        if winner == 1:
            text = "You Win!"
            color = RED
        elif winner == 2:
            text = "AI Wins!"
            color = YELLOW
        else:
            text = "It's a Tie!"
            color = WHITE
            
        # Draw text with shadow
        game_over_shadow = self.font.render(text, True, BLACK)
        game_over_text = self.font.render(text, True, color)
        shadow_rect = game_over_shadow.get_rect(center=(self.width//2 + 4, 204))
        text_rect = game_over_text.get_rect(center=(self.width//2, 200))
        self.screen.blit(game_over_shadow, shadow_rect)
        self.screen.blit(game_over_text, text_rect)
        
        self.restart_button.draw(self.screen)
        pygame.display.update()

    def draw_board(self):
        """Draw the game board."""
        self.screen.fill(BACKGROUND_COLOR)
        
        # Draw board background
        board_rect = pygame.Rect(0, SQUARESIZE, self.width, ROWS * SQUARESIZE)
        pygame.draw.rect(self.screen, BOARD_COLOR, board_rect)
        
        # Draw holes
        for c in range(COLS):
            for r in range(ROWS):
                center = (int(c*SQUARESIZE + SQUARESIZE/2), 
                         int((r+1)*SQUARESIZE + SQUARESIZE/2))
                # Draw hole shadow
                pygame.draw.circle(self.screen, (0, 0, 0, 128), 
                                 (center[0] + 2, center[1] + 2), RADIUS)
                # Draw hole
                pygame.draw.circle(self.screen, BLACK, center, RADIUS)

        # Draw pieces
        for c in range(COLS):
            for r in range(ROWS):
                center = (int(c*SQUARESIZE + SQUARESIZE/2), 
                         int((r+1)*SQUARESIZE + SQUARESIZE/2))
                if self.game.board[r][c] == 1:
                    # Draw piece shadow
                    pygame.draw.circle(self.screen, (200, 0, 0), 
                                     (center[0] + 2, center[1] + 2), RADIUS)
                    # Draw piece
                    pygame.draw.circle(self.screen, RED, center, RADIUS)
                elif self.game.board[r][c] == 2:
                    # Draw piece shadow
                    pygame.draw.circle(self.screen, (200, 200, 0), 
                                     (center[0] + 2, center[1] + 2), RADIUS)
                    # Draw piece
                    pygame.draw.circle(self.screen, YELLOW, center, RADIUS)
        
        pygame.display.update()

    def run(self):
        """Main game loop."""
        while True:
            if self.state == MENU:
                self.draw_menu()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    
                    if self.play_button.handle_event(event):
                        self.state = PLAYING
                        self.game = ConnectFour()
                        self.draw_board()
                        
            elif self.state == PLAYING:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                    if event.type == pygame.MOUSEMOTION and self.game.turn == 0 and not self.game.game_over:
                        pygame.draw.rect(self.screen, BACKGROUND_COLOR, 
                                       (0, 0, self.width, SQUARESIZE))
                        posx = event.pos[0]
                        # Draw piece shadow
                        pygame.draw.circle(self.screen, (200, 0, 0), 
                                         (posx + 2, int(SQUARESIZE/2) + 2), RADIUS)
                        # Draw piece
                        pygame.draw.circle(self.screen, RED, 
                                         (posx, int(SQUARESIZE/2)), RADIUS)
                        pygame.display.update()

                    if event.type == pygame.MOUSEBUTTONDOWN and self.game.turn == 0 and not self.game.game_over:
                        pygame.draw.rect(self.screen, BACKGROUND_COLOR, 
                                       (0, 0, self.width, SQUARESIZE))
                        posx = event.pos[0]
                        col = int(posx // SQUARESIZE)

                        if self.game.is_valid_location(col):
                            if self.game.drop_piece(col):
                                self.draw_board()
                                if self.game.game_over:
                                    self.state = GAME_OVER
                                    self.draw_game_over(self.game.winner)
                                else:
                                    self.game.turn = 1

                if self.game.turn == 1 and not self.game.game_over:
                    col, minimax_score = self.game.minimax(4, float('-inf'), float('inf'), True)
                    if self.game.is_valid_location(col):
                        if self.game.drop_piece(col):
                            self.draw_board()
                            if self.game.game_over:
                                self.state = GAME_OVER
                                self.draw_game_over(self.game.winner)
                            else:
                                self.game.turn = 0
                    
            elif self.state == GAME_OVER:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                        
                    if self.restart_button.handle_event(event):
                        self.state = PLAYING
                        self.game = ConnectFour()
                        self.draw_board()

if __name__ == "__main__":
    game = Game()
    game.run() 