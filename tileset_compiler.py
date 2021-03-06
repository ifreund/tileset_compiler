#!/usr/bin/env python3
"""
Tileset Compiler for Cataclysm Dark Days Ahead
"""

import os
import argparse
import json
from PIL import Image

parser = argparse.ArgumentParser(description="Compile a tileset for Cataclysm Dark Days Ahead")
parser.add_argument("path", help="path to the tileset")


def autotile_to_array(img, tile_width, tile_height):
    out = []
    if img is None:
        return out
    for row in range(0, img.height, tile_height):
        for column in range(0, img.width, tile_width):
            out.append(img.crop((column, row, column + tile_width, row + tile_height)))
    return out


# Loads and stores the tile definiton from path
class Tile_Def:
    id = []
    fg = []
    bg = []

    # TODO: implement alternates (and probably make fg/bg not lists
    alternates = []

    autotile_fg = None
    autotile_bg = None

    # TODO: may be able to drop these
    multitile = False
    rotates = False

    # filename must be a json file in root
    def __init__(self, root, filename, tile_def_in):
        filepath = os.path.join(root, filename)

        if "id" not in tile_def_in:
            print("Error reading {0}: missing \"id\" field".format(filepath))
            os.abort()
        if "fg" not in tile_def_in and "bg" not in tile_def_in:
            print("Error reading {0}: need at least one of \"fg\" or \"bg\"".format(filepath))
            os.abort()

        if isinstance(tile_def_in["id"], list):
            self.id = tile_def_in["id"]
        else:
            self.id = [tile_def_in["id"]]

        if "autotile" in tile_def_in and tile_def_in["autotile"]:
            self.multitile = True
            self.rotates = True
            if "fg" in tile_def_in:
                self.autotile_fg = Image.open(os.path.join(root, tile_def_in["fg"]))
            if "bg" in tile_def_in:
                self.autotile_bg = Image.open(os.path.join(root, tile_def_in["bg"]))
        else:
            if "rotates" in tile_def_in:
                self.rotates = tile_def_in["rotates"]

            if "fg" in tile_def_in:
                if isinstance(tile_def_in["fg"], list):
                    self.fg = map(Image.open, os.path.join(root, tile_def_in["fg"]))
                else:
                    self.fg = [Image.open(os.path.join(root, tile_def_in["fg"]))]

            if "bg" in tile_def_in:
                if isinstance(tile_def_in["bg"], list):
                    self.bg = map(Image.open, os.path.join(root, tile_def_in["bg"]))
                else:
                    self.bg = [Image.open(os.path.join(root, tile_def_in["bg"]))]



def main():
    args = parser.parse_args()
    out = {}
    out_dir = os.getcwd()
    for root, dirs, files in os.walk(args.path):

        if "tileset.txt" not in files:
            print("Error: missing \"tileset.txt\" in {0}".format(root))
            os.abort()
        else:
            with open(os.path.join(root, "tileset.txt"), "r") as fp:
                lines = fp.readlines()

                name_line_or_none = next((line for line in lines if line.startswith("NAME: ")), None).strip()
                if not name_line_or_none:
                    print("Error reading tileset.txt: Missing 'NAME:' statement")
                    os.abort()
                else:
                    out_dir = os.path.join(out_dir, name_line_or_none.split(" ")[1])
                    os.makedirs(out_dir, exist_ok=True)

                view_line_or_none = next((line for line in lines if line.startswith("VIEW: ")), None).strip()
                if not view_line_or_none:
                    print("Error reading tileset.txt: Missing 'VIEW:' statement")
                    os.abort()

                with open(os.path.join(out_dir, "tileset.txt"), "w") as tileset_txt:
                    tileset_txt.write("#Name of tileset\n")
                    tileset_txt.write(name_line_or_none + "\n")
                    tileset_txt.write("\n")
                    tileset_txt.write("#Viewing (Option) name of the tileset\n")
                    tileset_txt.write(view_line_or_none + "\n")
                    tileset_txt.write("\n")
                    tileset_txt.write("#JSON Path - Default of tile_config.json\n")
                    tileset_txt.write("JSON: tile_config.json\n")
                    tileset_txt.write("\n")
                    tileset_txt.write("#Tileset Path - Default of tinytile.png\n")
                    tileset_txt.write("TILESET: tiles.png\n")

        tile_height = 0
        tile_width = 0
        if "tile_info.json" not in files:
            print("Error: missing \"tile_info.json\" in {0}".format(root))
            os.abort()
        else:
            with open(os.path.join(root, "tile_info.json"), "r") as fp:
                tile_info = json.load(fp)

                out["tile_info"] = []
                out["tile_info"].append({})
                tile_height = tile_info["height"]
                tile_width = tile_info["width"]
                out["tile_info"][0]["height"] = tile_height
                out["tile_info"][0]["width"] = tile_width
                if "iso" in tile_info:
                    out["tile_info"][0]["iso"] = tile_info["iso"]
                if "pixelscale" in tile_info:
                    out["tile_info"][0]["pixelscale"] = tile_info["pixelscale"]

        out["tiles-new"] = []
        tile_index = 0
        for directory in dirs:
            current_file = {"file": directory + ".png"}
            sprite_width = tile_width
            sprite_height = tile_height

            dir_info_json = os.path.join(root, directory, directory + ".json")
            if not os.path.isfile(dir_info_json):
                print("Error: missing \"{0}\" file in {1}".format(dir_info_json, directory))
                os.abort()

            with open(dir_info_json, "r") as fp:
                tile_info = json.load(fp)

                if "file" in tile_info and tile_info["file"].endswith(".png"):
                    current_file["file"] = tile_info["file"]
                if "sprite_width" in tile_info:
                    sprite_width = tile_info["sprite_width"]
                    current_file["sprite_width"] = sprite_width
                if "sprite_height" in tile_info:
                    sprite_height = tile_info["sprite_height"]
                    current_file["sprite_height"] = sprite_height
                if "sprite_offset_x" in tile_info:
                    current_file["sprite_offset_x"] = tile_info["sprite_offset_x"]
                if "sprite_offset_y" in tile_info:
                    current_file["sprite_offset_y"] = tile_info["sprite_offset_y"]

            tile_defs = []
            print("Processing {0}".format(os.path.join(root, directory)))

            # Load EVERY json file in directory, regardless of folder structure
            for root2, dirs2, files2 in os.walk(os.path.join(root, directory)):
                for filename in files2:
                    cur_filepath = os.path.join(root2, filename)

                    # This file is special and doesn't contain a tile definition
                    if cur_filepath == dir_info_json:
                        continue

                    # Handles hidden files properly (won't open a file called ".json")
                    if os.path.splitext(cur_filepath)[-1].lower() == ".json":
                        with open(cur_filepath, "r") as fp:
                            tile_def_json = json.load(fp)
                            if isinstance(tile_def_json, list):
                                for tile_def in tile_def_json:
                                    tile_defs.append(Tile_Def(root2, filename, tile_def))
                            else:
                                tile_defs.append(Tile_Def(root2, filename, tile_def_json))

            tiles = []
            sprites = []
            for tile_def in tile_defs:
                tile = {}
                if len(tile_def.id) == 1:
                    tile["id"] = tile_def.id[0]
                else:
                    tile["id"] = tile_def.id

                # Autotile defintion
                if tile_def.autotile_fg is not None or tile_def.autotile_bg is not None:
                    tile["multitile"] = True
                    tile["rotates"] = True

                    fg_tiles = autotile_to_array(tile_def.autotile_fg, tile_width, tile_height)
                    bg_tiles = autotile_to_array(tile_def.autotile_bg, tile_width, tile_height)

                    unconnected = {}
                    unconnected["id"] = "unconnected"
                    if fg_tiles:
                        unconnected["fg"] = tile_index
                        tile["fg"] = tile_index
                        sprites.append(fg_tiles[15])
                        tile_index += 1
                    if bg_tiles:
                        unconnected["bg"] = tile_index
                        tile["bg"] = tile_index
                        sprites.append(bg_tiles[15])
                        tile_index += 1

                    center = {}
                    center["id"] = "center"
                    if fg_tiles:
                        center["fg"] = tile_index
                        sprites.append(fg_tiles[5])
                        tile_index += 1
                    if bg_tiles:
                        center["bg"] = tile_index
                        sprites.append(bg_tiles[5])
                        tile_index += 1

                    edge = {}
                    edge["id"] = "edge"
                    if fg_tiles:
                        edge["fg"] = [tile_index, tile_index + 1]
                        sprites.extend([fg_tiles[7], fg_tiles[13]])
                        tile_index += 2
                    if bg_tiles:
                        edge["bg"] = [tile_index, tile_index + 1]
                        sprites.extend([bg_tiles[7], bg_tiles[13]])
                        tile_index += 2

                    corner = {}
                    corner["id"] = "corner"
                    if fg_tiles:
                        corner["fg"] = [tile_index, tile_index + 1, tile_index + 2, tile_index + 3]
                        sprites.extend([fg_tiles[0], fg_tiles[8], fg_tiles[10], fg_tiles[2]])
                        tile_index += 4
                    if bg_tiles:
                        corner["bg"] = [tile_index, tile_index + 1, tile_index + 2, tile_index + 3]
                        sprites.extend([bg_tiles[0], bg_tiles[8], bg_tiles[10], bg_tiles[2]])
                        tile_index += 4

                    t_connection = {}
                    t_connection["id"] = "t_connection"
                    if fg_tiles:
                        t_connection["fg"] = [tile_index, tile_index + 1, tile_index + 2, tile_index + 3]
                        sprites.extend([fg_tiles[1], fg_tiles[4], fg_tiles[9], fg_tiles[6]])
                        tile_index += 4
                    if bg_tiles:
                        t_connection["bg"] = [tile_index, tile_index + 1, tile_index + 2, tile_index + 3]
                        sprites.extend([bg_tiles[1], bg_tiles[4], bg_tiles[9], bg_tiles[6]])
                        tile_index += 4

                    end_piece = {}
                    end_piece["id"] = "end_piece"
                    if fg_tiles:
                        end_piece["fg"] = [tile_index, tile_index + 1, tile_index + 2, tile_index + 3]
                        sprites.extend([fg_tiles[3], fg_tiles[12], fg_tiles[11], fg_tiles[14]])
                        tile_index += 4
                    if bg_tiles:
                        end_piece["bg"] = [tile_index, tile_index + 1, tile_index + 2, tile_index + 3]
                        sprites.extend([bg_tiles[3], bg_tiles[12], bg_tiles[11], bg_tiles[14]])
                        tile_index += 4

                    tile["additional_tiles"] = [unconnected, center, edge, corner, t_connection, end_piece]
                else:
                    if tile_def.fg:
                        if len(tile_def.fg) == 1:
                            tile["fg"] = tile_index
                            sprites.append(tile_def.fg[0])
                            tile_index += 1
                        else:
                            tile["fg"] = []
                            for sprite in tile_def.fg:
                                tile["fg"].append(tile_index)
                                sprites.append(sprite)
                                tile_index += 1

                    if tile_def.bg:
                        if len(tile_def.bg) == 1:
                            tile["bg"] = tile_index
                            sprites.append(tile_def.bg[0])
                            tile_index += 1
                        else:
                            tile["bg"] = []
                            for sprite in tile_def.bg:
                                tile["bg"].append(tile_index)
                                sprites.append(sprite)
                                tile_index += 1
                    tile["rotates"] = False

                tiles.append(tile)

            current_file["tiles"] = tiles
            out["tiles-new"].append(current_file)

            atlas_width = 16 if len(sprites) > 16 else len(sprites)
            atlas_height = len(sprites) // 16 + 1

            # create transparent
            atlas = Image.new("RGBA", (atlas_width * sprite_width, atlas_height * sprite_height), (255, 0, 0, 0))

            i = 0
            for sprite in sprites:
                atlas.paste(sprite, (i % atlas_width * sprite_width, i // atlas_width * sprite_height))
                i += 1

            atlas.save(os.path.join(out_dir, current_file["file"]), format="PNG")

        break  # os.walk

    # write output
    with open(os.path.join(out_dir, "tile_config.json"), "w") as tile_config_json:
        json.dump(out, tile_config_json, indent=2)


if __name__ == "__main__":
    main()
