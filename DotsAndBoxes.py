import pygame
import math
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
EDGE_WIDTH = 10
INACTIVE_EDGE_COLOR = (70, 70, 70)
ACTIVE_EDGE_COLOR = (200, 200, 200)
VERTEX_RADIUS = 16
VERTEX_COLOR = (255, 255, 255)
PLAYER_COLORS = [(255, 0, 0), (0, 0, 255)]
TEXT_COLOR = (255, 255, 255)
INFO_FONT = pygame.font.Font(None, 28)
PLAYER_FONT = pygame.font.Font(None, 36)
BUTTON_FONT = pygame.font.Font(None, 28)
GAME_OVER_DELAY = 3000  # Delay in milliseconds

# Undo and redo button constants
UNDO_BUTTON_POS = (50, SCREEN_HEIGHT - 50)
UNDO_BUTTON_SIZE = (80, 40)
UNDO_BUTTON_COLOR = (0, 200, 0)
UNDO_BUTTON_TEXT_COLOR = (255, 255, 255)
REDO_BUTTON_POS = (150, SCREEN_HEIGHT - 50)
REDO_BUTTON_COLOR = (200, 0, 0)

# Setup the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Wheel Graph Dots and Boxes')


def prompt_for_spokes():
    input_box = pygame.Rect(SCREEN_WIDTH / 2 - 100, SCREEN_HEIGHT / 2 - 10, 200, 30)
    active = False  # Input box is not active
    text = ''
    label_text = 'Enter the number of spokes (3 or more):'
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        try:
                            n_spokes = int(text)
                            return max(3, n_spokes)  # Ensure a minimum of 3 spokes
                        except ValueError:
                            return 3  # Default to 3 spokes if input is invalid
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode

        screen.fill((30, 30, 30))  # Dark grey background
        # Render the label text
        label_surface = INFO_FONT.render(label_text, True, TEXT_COLOR)
        screen.blit(label_surface, (SCREEN_WIDTH / 2 - label_surface.get_width() / 2, SCREEN_HEIGHT / 2 - 40))
        # Render the current text
        txt_surface = INFO_FONT.render(text, True, color)
        # Adjust the width of the box if text is too long
        input_box.w = max(200, txt_surface.get_width() + 10)
        # Blit the input text
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        # Blit the input box
        pygame.draw.rect(screen, color, input_box, 2)

        pygame.display.flip()


def create_wheel_graph_edges_and_vertices(n_spokes):
    edges = {}
    vertices = {}
    center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    # Add center vertex
    vertices[center] = False

    angle_step = (2 * math.pi) / n_spokes
    outer_vertices = []

    # Create outer vertices and connect them to the center
    for i in range(n_spokes):
        angle = i * angle_step
        x = center[0] + ((SCREEN_WIDTH // 4) * math.cos(angle))
        y = center[1] + ((SCREEN_HEIGHT // 4) * math.sin(angle))
        outer_vertex = (int(x), int(y))
        outer_vertices.append(outer_vertex)
        vertices[outer_vertex] = False
        edges[(center, outer_vertex)] = True

    # Connect outer vertices to form a cycle
    for i in range(n_spokes):
        start_vertex = outer_vertices[i]
        end_vertex = outer_vertices[(i + 1) % n_spokes]
        edges[(start_vertex, end_vertex)] = True

    return edges, vertices


def draw_wheel_graph(edges, vertices, n_spokes, current_player):
    # Draw the number of spokes at the top
    spoke_text = INFO_FONT.render(f'Spokes: {n_spokes}', True, TEXT_COLOR)
    screen.blit(spoke_text, (5, 5))

    # Draw whose turn at the bottom
    turn_text = PLAYER_FONT.render(f'Player {current_player + 1} Turn', True, PLAYER_COLORS[current_player])
    screen.blit(turn_text, (SCREEN_WIDTH // 2 - turn_text.get_width() // 2, SCREEN_HEIGHT - 35))

    # Draw edges
    for (start_pos, end_pos), active in edges.items():
        color = ACTIVE_EDGE_COLOR if active else INACTIVE_EDGE_COLOR
        pygame.draw.line(screen, color, start_pos, end_pos, EDGE_WIDTH)

    # Draw vertices
    for position, player in vertices.items():
        color = VERTEX_COLOR if not player else PLAYER_COLORS[0] if player == 'player 1' else PLAYER_COLORS[1]
        pygame.draw.circle(screen, color, position, VERTEX_RADIUS)


def get_clicked_edge(edges, mouse_pos):
    for (start_pos, end_pos), active in edges.items():
        if not active:
            continue
        nearest_point = get_nearest_point_on_line(start_pos, end_pos, mouse_pos)
        distance_sq = (mouse_pos[0] - nearest_point[0]) ** 2 + (mouse_pos[1] - nearest_point[1]) ** 2
        if distance_sq <= (EDGE_WIDTH // 2) ** 2:
            return (start_pos, end_pos)
    return None


def get_nearest_point_on_line(a, b, p):
    ap = (p[0] - a[0], p[1] - a[1])
    ab = (b[0] - a[0], b[1] - a[1])
    ab_mag = (ab[0] ** 2 + ab[1] ** 2) ** 0.5
    ab_unit = (ab[0] / ab_mag, ab[1] / ab_mag)
    distance = ap[0] * ab_unit[0] + ap[1] * ab_unit[1]
    distance = max(0, min(ab_mag, distance))
    nearest = (a[0] + ab_unit[0] * distance, a[1] + ab_unit[1] * distance)
    return nearest


def check_for_isolated_vertices(vertices, edges, current_player):
    player_tag = 'player 1' if current_player == 0 else 'player 2'
    isolated_vertex_count = 0
    for vertex in vertices:
        if vertices[vertex] is False:  # Vertex is not owned yet
            # Check if all edges connected to this vertex are inactive
            connected_edges = [edge for edge in edges if vertex in edge]
            if all(not edges[edge] for edge in connected_edges):
                vertices[vertex] = player_tag  # Assign vertex to player
                isolated_vertex_count += 1  # Increment the isolated vertex count
    return isolated_vertex_count


def draw_buttons(current_player):
    # Draw the undo button
    pygame.draw.rect(screen, UNDO_BUTTON_COLOR, (*UNDO_BUTTON_POS, *UNDO_BUTTON_SIZE))
    undo_text = BUTTON_FONT.render('Undo', True, UNDO_BUTTON_TEXT_COLOR)
    screen.blit(undo_text, undo_text.get_rect(center=(UNDO_BUTTON_POS[0] + UNDO_BUTTON_SIZE[0] // 2, UNDO_BUTTON_POS[1] + UNDO_BUTTON_SIZE[1] // 2)))

    # Draw the redo button
    pygame.draw.rect(screen, REDO_BUTTON_COLOR, (*REDO_BUTTON_POS, *UNDO_BUTTON_SIZE))
    redo_text = BUTTON_FONT.render('Redo', True, UNDO_BUTTON_TEXT_COLOR)
    screen.blit(redo_text, redo_text.get_rect(center=(REDO_BUTTON_POS[0] + UNDO_BUTTON_SIZE[0] // 2, REDO_BUTTON_POS[1] + UNDO_BUTTON_SIZE[1] // 2)))

def get_button_clicked(position):
    # Check if the undo or redo button was clicked
    undo_button_rect = pygame.Rect(UNDO_BUTTON_POS[0], UNDO_BUTTON_POS[1], UNDO_BUTTON_SIZE[0], UNDO_BUTTON_SIZE[1])
    redo_button_rect = pygame.Rect(REDO_BUTTON_POS[0], REDO_BUTTON_POS[1], UNDO_BUTTON_SIZE[0], UNDO_BUTTON_SIZE[1])
    if undo_button_rect.collidepoint(position):
        return 'undo'
    elif redo_button_rect.collidepoint(position):
        return 'redo'
    return None

def undo_move(move_history, redo_stack, current_state):
    if move_history:
        last_state = move_history.pop()
        redo_stack.append(current_state)
        return last_state
    return current_state

def redo_move(redo_stack, move_history, current_state):
    if redo_stack:
        next_state = redo_stack.pop()
        move_history.append(current_state)
        return next_state
    return current_state

def game_loop(n_spokes):
    edges, vertices = create_wheel_graph_edges_and_vertices(n_spokes)
    current_player = 0
    player_scores = [0, 0]
    running = True
    clock = pygame.time.Clock()
    move_history = []  # Store the state after each move
    redo_stack = []  # Store the state after each undo

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                clicked_button = get_button_clicked(mouse_pos)
                if clicked_button == 'undo':
                    edges, vertices, current_player = undo_move(move_history, redo_stack, (edges, vertices, current_player))
                elif clicked_button == 'redo':
                    edges, vertices, current_player = redo_move(redo_stack, move_history, (edges, vertices, current_player))
                else:
                    redo_stack.clear()  # Clear the redo stack if a new move is made
                    clicked_edge = get_clicked_edge(edges, mouse_pos)
                    if clicked_edge and edges[clicked_edge]:
                        move_history.append((edges.copy(), vertices.copy(), current_player))
                        edges[clicked_edge] = False
                        isolated_vertices_changed = check_for_isolated_vertices(vertices, edges, current_player)
                        if not isolated_vertices_changed:
                            current_player = 1 - current_player  # Change turn if no vertex isolated
                        else:
                            player_scores[current_player] += isolated_vertices_changed  # Increment player's score by number of isolated vertices

        # Redraw game state before checking for game over
        screen.fill((0, 0, 0))
        draw_wheel_graph(edges, vertices, n_spokes, current_player)
        draw_buttons(current_player)
        pygame.display.flip()
        
        # Check for game over condition after updating display
        if not any(edges.values()):  # No active edges left
            running = False  # End the game after the last move is rendered

        clock.tick(60)

    # Display the game over state after exiting main loop
    game_over(player_scores)

def game_over(player_scores):
    # Use a semi-transparent surface to darken the screen slightly
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))  # Semi-transparent black
    screen.blit(overlay, (0, 0))

    # Decide the game over text and color (red in this case)
    if player_scores[0] > player_scores[1]:
        winner_text = "Player 1 wins!"
    elif player_scores[1] > player_scores[0]:
        winner_text = "Player 2 wins!"
    else:
        winner_text = "It's a tie!"
    
    # Set the color to red
    text_color = (255, 0, 0)

    # Create a text surface with the winner message
    text_surface = PLAYER_FONT.render(winner_text, True, text_color)
    # Position the text in the center of the screen
    text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

    # Blit the text surface onto the screen
    screen.blit(text_surface, text_rect)
    pygame.display.flip()  # Update the display with the new overlay

    pygame.time.wait(GAME_OVER_DELAY)  # Wait for a few seconds before continuing


def main():
    while True:
        n_spokes = prompt_for_spokes()
        game_loop(n_spokes)


if __name__ == '__main__':
    main()