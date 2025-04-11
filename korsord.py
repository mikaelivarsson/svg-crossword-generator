#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import svgwrite
from svgwrite.extensions import Inkscape
import argparse
from textwrap import wrap
from datetime import datetime

highlightcolor = 'lightsteelblue'
clue_font = 10

def read_input(filename):
    with open(filename, 'r') as file:
        content = file.read()
    # split sections separated by blank lines
    sections = content.split('\n\n')

    if len(sections) < 4:
        raise ValueError("Input file must contain four sections: words, clues, highlights and decorations.")

    words_section = sections[0].splitlines()
    clues_section = sections[1].splitlines()
    highlights_section = sections[2].splitlines()
    decorations_section = sections[3].splitlines()

    words = [line.rstrip('\n').upper() for line in words_section]

    clues_with_positions = []
    for line in clues_section:
        parts = line.split(maxsplit=2)
        if len(parts) < 3:
            raise ValueError("Each clue line must contain a position, font size, and a clue text.")
        position = parts[0]
        font_size = int(parts[1])
        clue = parts[2]
        start_position = position[:-2]
        direction = position[-2]
        span = int(position[-1])
        clues_with_positions.append((clue, start_position, direction, span, font_size))

    highlighted_positions = [line.strip() for line in highlights_section]
    decorations = [(line.split()[0], line.split()[1]) for line in decorations_section]

    return words, clues_with_positions, highlighted_positions, decorations

def read_words_from_file(filename):
    with open(filename, 'r') as file:
        # keep lines as is including spaces
        words = [line.rstrip('\n').upper() for line in file]
    return words

def read_clues_from_file(filename):
    clues_with_positions = []
    with open(filename, 'r') as file:
        for line in file:
            parts = line.strip().split(maxsplit=2)
            position, clue = parts[0], parts[1]
            font_size = int(parts[2]) if len(parts) > 2 else clue_font_size
            start_position = position[:-2]
            direction = position[-2]
            span = int(position[-1])
            clues_with_positions.append((clue, start_position, direction, span, font_size))
    return clues_with_positions

def read_highlights(filename):
    highlighted = []
    with open(filename, 'r') as file:
        for line in file:
            highlighted.append(line.strip())
    return highlighted

def read_decorations(filename):
    decorations = []
    with open(filename, 'r') as file:
        for line in file:
            position, command = line.strip().split()
            decorations.append((position, command))
    return decorations

def alpha_to_index(position):
    col, row = position[0], position[1:]
    col_index = ord(col.upper()) - ord('A')
    row_index = int(row) - 1
    return row_index, col_index

def create_grid_from_words(words):
    # determine grid dimensions based on longest line
    max_len = max(len(word) for word in words)
    grid_size = len(words)
    # create empty grid
    grid = [['' for _ in range(max_len)] for _ in range(grid_size)]
    # fill the grid with characters from words, preserving spaces
    for i, word in enumerate(words):
        for j, char in enumerate(word):
            grid[i][j] = '' if char == ' ' else char
    return grid

def create_clue_grid(clues_with_positions, grid_size):
    grid = [['' for _ in range(grid_size)] for _ in range(grid_size)]
    merged_cells = set()
    clue_boxes = []
    for clue, position, direction, span, font_size in clues_with_positions:
        row_index, col_index = alpha_to_index(position)
        # place clue only once and note which are merged cells, determine the covered area
        if direction.upper() == 'H':
            grid[row_index][col_index] = clue
            clue_boxes.append((row_index, col_index, row_index, col_index + span - 1, clue, font_size))
            for i in range(1, span):
                merged_cells.add((row_index, col_index + i))
        elif direction.upper() == 'V':
            grid[row_index][col_index] = clue
            clue_boxes.append((row_index, col_index, row_index + span - 1, col_index, clue, font_size))
            for i in range(1, span):
                merged_cells.add((row_index + i, col_index))
    return grid, merged_cells, clue_boxes

def wrap_text(text, max_width, font_size):
    """ wrap text so it fits in a cell """
    wrapped = []
    lines = text.split('\\n')
    lines = [line if line != '' else '\n' for line in lines]
    max_chars_per_line = max_width // (font_size // 2)
    for line in lines:
        if line == '\n':
            wrapped.append('')
        else:
            wrapped.extend(wrap(line, max_chars_per_line))
    return wrapped

def draw_arrow(dwg, start_pos, end_pos):
    direction_x = end_pos[0] - start_pos[0]
    direction_y = end_pos[1] - start_pos[1]
    length = (direction_x ** 2 + direction_y ** 2) ** 0.5
    if length == 0:
        return
    unit_x = direction_x / length
    unit_y = direction_y / length
    shaft_end_x = end_pos[0] - unit_x * 3
    shaft_end_y = end_pos[1] - unit_y * 3
    dwg.add(dwg.line(start=start_pos, end=(shaft_end_x, shaft_end_y), stroke='black'))
    arrow_base_x = end_pos[0] - unit_x * 5
    arrow_base_y = end_pos[1] - unit_y * 5
    normal_x = -unit_y
    normal_y = unit_x
    left_x = arrow_base_x + normal_x * 5 / 2
    left_y = arrow_base_y + normal_y * 5 / 2
    right_x = arrow_base_x - normal_x * 5 / 2
    right_y = arrow_base_y - normal_y * 5 / 2
    dwg.add(dwg.polygon(points=[end_pos, (left_x, left_y), (right_x, right_y)], fill='black'))

def draw_line(dwg, start_pos, end_pos, stroke_width=1):
    dwg.add(dwg.line(start=start_pos, end=end_pos, stroke='black', stroke_width=stroke_width))

def draw_dividerh(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x, top_left_y + cell_size/2)
    line_end = (top_left_x + cell_size, top_left_y + cell_size/2)
    draw_line(dwg, line_start, line_end)

def draw_dh2(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x, top_left_y + cell_size/2 -3)
    line_end = (top_left_x + cell_size, top_left_y + cell_size/2 -3)
    draw_line(dwg, line_start, line_end)

def draw_dh3(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x, top_left_y + cell_size/2 +3)
    line_end = (top_left_x + cell_size, top_left_y + cell_size/2 +3)
    draw_line(dwg, line_start, line_end)

def draw_dh4(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x, top_left_y + cell_size/2 -7)
    line_end = (top_left_x + cell_size, top_left_y + cell_size/2 -7)
    draw_line(dwg, line_start, line_end)

def draw_dividerv(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x + cell_size/2, top_left_y)
    line_end = (top_left_x + cell_size/2, top_left_y + cell_size)
    draw_line(dwg, line_start, line_end)

def draw_continuer(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x + 5, top_left_y + 28)
    line_end = (top_left_x + 5, top_left_y + 35)
    arrow_start = (top_left_x + 5, top_left_y + 34.5)
    arrow_end = (top_left_x + 13, top_left_y + 34.5)
    draw_line(dwg, line_start, line_end)
    draw_arrow(dwg, arrow_start, arrow_end)

def draw_continuel(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x+cell_size - 5, top_left_y + 28)
    line_end = (top_left_x+cell_size - 5, top_left_y + 35)
    arrow_start = (top_left_x+cell_size - 5, top_left_y + 34.5)
    arrow_end = (top_left_x+cell_size - 13, top_left_y + 34.5)
    draw_line(dwg, line_start, line_end)
    draw_arrow(dwg, arrow_start, arrow_end)

def draw_continued(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x + 30, top_left_y + 3)
    line_end = (top_left_x + 35, top_left_y + 3)
    arrow_start = (top_left_x + 35, top_left_y + 2.5)
    arrow_end = (top_left_x + 35, top_left_y + 11)
    draw_line(dwg, line_start, line_end)
    draw_arrow(dwg, arrow_start, arrow_end)

def draw_arrowdown(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x + 20, top_left_y + 37)
    line_end = (top_left_x + 20, top_left_y + 47)
    draw_arrow(dwg, line_start, line_end)

def draw_arrowup(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x + 20, top_left_y +3)
    line_end = (top_left_x + 20, top_left_y -7)
    draw_arrow(dwg, line_start, line_end)

def draw_arrowright(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x + 37, top_left_y + 20)
    line_end = (top_left_x + 47, top_left_y + 20)
    draw_arrow(dwg, line_start, line_end)

def draw_arrowrd(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x + 37, top_left_y + 37)
    line_end = (top_left_x + 44, top_left_y + 44)
    arrow_start = (top_left_x + 43.8, top_left_y + 43.5)
    arrow_end = (top_left_x + 43.8, top_left_y + 52)
    draw_line(dwg, line_start, line_end)
    draw_arrow(dwg, arrow_start, arrow_end)

def draw_arrowrr(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x + 37, top_left_y + 37)
    line_end = (top_left_x + 44, top_left_y + 44)
    arrow_start = (top_left_x + 43.8, top_left_y + 44)
    arrow_end = (top_left_x + 52, top_left_y + 44)
    draw_line(dwg, line_start, line_end)
    draw_arrow(dwg, arrow_start, arrow_end)

def draw_arrowur(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x + 3, top_left_y + 7)
    line_end = (top_left_x + 3, top_left_y - 5)
    arrow_start = (top_left_x + 2.5, top_left_y - 5)
    arrow_end = (top_left_x + 10, top_left_y - 5)
    draw_line(dwg, line_start, line_end)
    draw_arrow(dwg, arrow_start, arrow_end)

def draw_arrowdr(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x + 3, top_left_y + cell_size - 7)
    line_end = (top_left_x + 3, top_left_y + cell_size + 5)
    arrow_start = (top_left_x + 2.5, top_left_y + cell_size + 5)
    arrow_end = (top_left_x + 10, top_left_y + cell_size + 5)
    draw_line(dwg, line_start, line_end)
    draw_arrow(dwg, arrow_start, arrow_end)

def draw_trid(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    x = col * cell_size
    y = row * cell_size
    triangle_coordinates = [(x + 15, y), (x + 25, y), (x + 20, y + 5)]
    dwg.add(dwg.polygon(points=triangle_coordinates, fill='white', stroke='black', stroke_width=1))

def draw_trir(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    x = col * cell_size
    y = row * cell_size
    triangle_coordinates = [(x, y + 15), (x, y + 25), (x + 5, y + 20)]
    dwg.add(dwg.polygon(points=triangle_coordinates, fill='white', stroke='black', stroke_width=1))

def draw_lineh(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x, top_left_y + cell_size/2)
    line_end = (top_left_x + cell_size, top_left_y + cell_size/2)
    draw_line(dwg, line_start, line_end, stroke_width=4)

def draw_brd(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x, top_left_y + cell_size/2)
    line_end = (top_left_x + cell_size/2, top_left_y + cell_size/2)
    draw_line(dwg, line_start, line_end, stroke_width=4)
    line_start = (top_left_x + cell_size/2, top_left_y + cell_size/2 - 2)
    line_end = (top_left_x + cell_size/2, top_left_y + cell_size - 5)
    draw_line(dwg, line_start, line_end, stroke_width=4)
    x = top_left_x
    y = top_left_y
    tri_cords = [(x+12, y+cell_size-10), (x+cell_size-12, y+cell_size-10), 
            (x+cell_size/2, y+cell_size-1)]
    dwg.add(dwg.polygon(points=tri_cords, fill='black', stroke='black', stroke_width='1'))

def draw_br(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x, top_left_y + cell_size/2)
    line_end = (top_left_x + 4*cell_size/5, top_left_y + cell_size/2)
    draw_line(dwg, line_start, line_end, stroke_width=4)
    x = top_left_x
    y = top_left_y
    tri_cords = [(x+cell_size-10, y+12), (x+cell_size-10, y+cell_size-12), 
            (x+cell_size-1, y+cell_size/2)]
    dwg.add(dwg.polygon(points=tri_cords, fill='black', stroke='black', stroke_width='1'))

def draw_bur(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    top_left_x = col * cell_size
    top_left_y = row * cell_size
    line_start = (top_left_x+cell_size/2, top_left_y + cell_size/2)
    line_end = (top_left_x + 4*cell_size/5, top_left_y + cell_size/2)
    draw_line(dwg, line_start, line_end, stroke_width=4)
    line_start = (top_left_x+cell_size/2, top_left_y + cell_size/2-2)
    line_end = (top_left_x+cell_size/2, top_left_y + cell_size)
    draw_line(dwg, line_start, line_end, stroke_width=4)
    x = top_left_x
    y = top_left_y
    tri_cords = [(x+cell_size-10, y+12), (x+cell_size-10, y+cell_size-12), 
            (x+cell_size-1, y+cell_size/2)]
    dwg.add(dwg.polygon(points=tri_cords, fill='black', stroke='black', stroke_width='1'))

def draw_copyright(dwg, alpha, cell_size=40):
    row, col = alpha_to_index(alpha)
    x = col * cell_size
    y = row * cell_size
    dwg.add(dwg.rect(insert=(x, y), size=(cell_size, cell_size), fill='black'))
    year = datetime.now().year
    copyright_text = f"© Mikael Ivarsson {year}"
    wrapped_copyright = wrap_text(copyright_text, cell_size, font_size=10)
    text_height = len(wrapped_copyright * 10)
    vertical_offset = (cell_size - text_height) / 2 + 8
    for i, line in enumerate(wrapped_copyright):
        dwg.add(dwg.text(line,
                         insert=(x + cell_size / 2, y + vertical_offset + (i * 10)),
                         text_anchor="middle",
                         font_size=10,
                         font_family='Arial',
                         fill='white'))

def create_crossword(filename, grid, clue_grid, highlighted_positions, merged_cells, clue_boxes, decorations, hide_words = False, cell_size=40):
    # calculate size of the grid
    num_rows = len(grid)
    num_cols = len(grid[0]) if num_rows > 0 else 0

    # create an svg drawing object
    dwg = svgwrite.Drawing(filename, profile='full', size=(cell_size * num_cols, cell_size * num_rows))
    inkscape = Inkscape(dwg)
    words_layer = inkscape.layer(label="Words", locked=False)

    #font_family = 'Knewave' # ok but abit too bold..
    font_family = 'Mogra'

    highlighted_indices = [alpha_to_index(pos) for pos in highlighted_positions]

    dwg.defs.add(dwg.style(f'@import url(\'https://fonts.googleapis.com/css2?family={font_family}&display=swap\');'))

    # draw the grid and fill in the letters
    for row in range(num_rows):
        for col in range(num_cols):
            if(row, col) in merged_cells:
                continue # skip merged cells
            x = col*cell_size
            y = row*cell_size

            fill_color = highlightcolor if (row, col) in highlighted_indices else 'white'

            # Check if the current cell is part of a clue box
            is_clue_box = False
            box_width = cell_size
            box_height = cell_size

            for start_row, start_col, end_row, end_col, _, _ in clue_boxes:
                if start_row == row and start_col <= col <= end_col and start_row == end_row:
                    is_clue_box = True
                    box_width = (end_col - start_col + 1) * cell_size
                    box_height = cell_size # Horizontal clue box
                    break
                elif start_col == col and start_row <= row <= end_row and start_col == end_col:
                    is_clue_box = True
                    box_width = cell_size # Vertical clue box
                    box_height = (end_row - start_row + 1) * cell_size
                    break

            # Draw rectangle for clue box cells
            dwg.add(dwg.rect(insert=(x, y), size=(box_width, box_height), fill=fill_color, stroke='black'))
            # if the cell contains a letter, add the letter text, if not hidden
            if not hide_words:
                if grid[row][col] != '':
                    words_layer.add(dwg.text(
                        grid[row][col],
                        insert=(x + cell_size/2, y + cell_size/2 + 10),
                        text_anchor="middle",
                        font_size=30,
                        font_family=font_family,
                        fill='black'
                    ))

    dwg.add(words_layer)

    # draw clue boxes and wrap text in them
    for(start_row, start_col, end_row, end_col, clue, font_size) in clue_boxes:
        x = start_col * cell_size
        y = start_row * cell_size
        box_width = (end_col - start_col + 1) * cell_size
        box_height = (end_row - start_row + 1) * cell_size

        fill_color = 'white'
#        dwg.add(dwg.rect(insert=(x,y), size=(box_width, box_height), fill=fill_color, stroke='black'))
        # wrap and draw the clue text
        if start_row == end_row:
            wrapped_clue = wrap_text(clue, box_width, font_size=font_size)
        else:
            wrapped_clue = wrap_text(clue, box_height, font_size=font_size)

        clue_height = len(wrapped_clue) * font_size
        vertical_offset = (box_height - clue_height) / 2 + font_size

        for i, line in enumerate(wrapped_clue):
            dwg.add(dwg.text(line,
                             insert=(x + box_width / 2, y + vertical_offset + (i * font_size)),
                             text_anchor = "middle",
                             font_size=font_size,
                             font_family = font_family,
                             fill='black'))

    for position, command in decorations:
        if command == 'CR':
            draw_continuer(dwg, position)
        elif command == 'CD':
            draw_continued(dwg, position)
        elif command == 'CL':
            draw_continuel(dwg, position)
        elif command == 'AR':
            draw_arrowright(dwg, position)
        elif command == 'AD':
            draw_arrowdown(dwg, position)
        elif command == 'AU':
            draw_arrowup(dwg, position)
        elif command == 'RR':
            draw_arrowrr(dwg, position)
        elif command == 'RD':
            draw_arrowrd(dwg, position)
        elif command == 'UR':
            draw_arrowur(dwg, position)
        elif command == 'DR':
            draw_arrowdr(dwg, position)
        elif command == 'TR':
            draw_trir(dwg, position)
        elif command == 'TD':
            draw_trid(dwg, position)
        elif command == 'C':
            draw_copyright(dwg, position)
        elif command == 'DH':
            draw_dividerh(dwg, position)
        elif command == 'DV':
            draw_dividerv(dwg, position)
        elif command == 'LH':
            draw_lineh(dwg, position)
        elif command == 'BRD':
            draw_brd(dwg, position)
        elif command == 'BR':
            draw_br(dwg, position)
        elif command == 'BUR':
            draw_bur(dwg, position)
        elif command == 'DH2':
            draw_dh2(dwg, position)
        elif command == 'DH3':
            draw_dh3(dwg, position)
        elif command == 'DH4':
            draw_dh4(dwg, position)

    dwg.save()

def main():
    parser = argparse.ArgumentParser(description='Generate a Swedish crossword SVG from a text file.')
    parser.add_argument('input_file', help='The path to the input text file with words.')
#    parser.add_argument('clue_file', help='The path to the input text file with clues.')
#    parser.add_argument('highlight_file', help='The path to the input text file with highlights.')
#    parser.add_argument('decorations_file', help='The path to the input text file with highlights.')

    args = parser.parse_args()
    output_file = args.input_file.split('.')[0] + '.svg'
    output_file_facit = args.input_file.split('.')[0] + '_facit.svg'

 #   words = read_words_from_file(args.input_file)
 #   clues_with_positions = read_clues_from_file(args.clue_file)
 #   highlighted_positions = read_highlights(args.highlight_file)
 #   decorations = read_decorations(args.decorations_file)

    words, clues_with_positions, highlighted_positions, decorations = read_input(args.input_file)
    grid = create_grid_from_words(words)
    max_grid_size = max(len(grid), len(grid[0]))
    clue_grid, merged_cells, clue_boxes = create_clue_grid(clues_with_positions, max_grid_size)

    create_crossword(output_file_facit, grid, clue_grid, highlighted_positions, merged_cells, clue_boxes, decorations, hide_words = False)
#    create_crossword(output_file, grid, clue_grid, highlighted_positions, merged_cells, clue_boxes, decorations, hide_words = True)
if __name__ == '__main__':
    main()
