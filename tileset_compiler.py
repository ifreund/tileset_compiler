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
    for x in range(0, img.width, tile_width):
        for y in range(0, img.height, tile_height):
            out.append(img.crop((x, y, x + tile_width, y + tile_height)))
    return out


def autotile_to_tile_config(sprites, fg, bg, tile_width, tile_height):
    fg_tiles = autotile_to_array(fg, tile_width, tile_height)
    bg_tiles = autotile_to_array(bg, tile_width, tile_height)

    unconnected = {}
    unconnected["id"] = "unconnected"
    if fg:
        unconnected["fg"] = len(sprites)
        sprites.append(fg_tiles[3])
    if bg:
        unconnected["bg"] = len(sprites)
        sprites.append(bg_tiles[3])

    center = {}
    center["id"] = "center"
    if fg:
        center["fg"] = len(sprites)
        sprites.append(fg_tiles[5])
    if bg:
        center["bg"] = len(sprites)
        sprites.append(bg_tiles[5])

    edge = {}
    edge["id"] = "edge"
    if fg:
        edge["fg"] = [len(sprites), len(sprites) + 1]
        sprites.extend([fg_tiles[7], fg_tiles[11]])
    if bg:
        edge["bg"] = [len(sprites), len(sprites) + 1]
        sprites.extend([bg_tiles[7], bg_tiles[11]])

    corner = {}
    corner["id"] = "corner"
    if fg:
        corner["fg"] = [len(sprites), len(sprites) + 1, len(sprites) + 2, len(sprites) + 3]
        sprites.extend([fg_tiles[0], fg_tiles[2], fg_tiles[8], fg_tiles[10]])
    if bg:
        corner["bg"] = [len(sprites), len(sprites) + 1, len(sprites) + 2, len(sprites) + 3]
        sprites.extend([bg_tiles[0], bg_tiles[2], bg_tiles[8], bg_tiles[10]])

    t_connection = {}
    t_connection["id"] = "t_connection"
    if fg:
        t_connection["fg"] = [len(sprites), len(sprites) + 1, len(sprites) + 2, len(sprites) + 3]
        sprites.extend([fg_tiles[1], fg_tiles[4], fg_tiles[6], fg_tiles[9]])
    if bg:
        t_connection["bg"] = [len(sprites), len(sprites) + 1, len(sprites) + 2, len(sprites) + 3]
        sprites.extend([bg_tiles[1], bg_tiles[4], bg_tiles[6], bg_tiles[9]])

    end_piece = {}
    end_piece["id"] = "end_piece"
    if fg:
        end_piece["fg"] = [len(sprites), len(sprites) + 1, len(sprites) + 2, len(sprites) + 3]
        sprites.extend([fg_tiles[12], fg_tiles[13], fg_tiles[14], fg_tiles[15]])
    if bg:
        end_piece["bg"] = [len(sprites), len(sprites) + 1, len(sprites) + 2, len(sprites) + 3]
        sprites.extend([bg_tiles[12], bg_tiles[13], bg_tiles[14], bg_tiles[15]])

    return [unconnected, center, edge, corner, t_connection, end_piece]


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

    def __init__(self, path):
        contents = os.listdir(path)
        json_or_none = next((f for f in contents if f.endswith(".json")), None)
        if not json_or_none:
            print("Error: missing json file in {0}".format(path))
            os.exit(1)
        else:
            with open(os.path.join(path, json_or_none), "r") as fp:
                tile_def_in = json.load(fp)

                if "id" not in tile_def_in:
                    print("Error reading {0}: missing id".format(os.path.join(path, json_or_none)))
                    os.exit(1)
                if "fg" not in tile_def_in and "bg" not in tile_def_in:
                    print("Error reading {0}: need at least one of fg or bg".format(os.path.join(path, json_or_none)))
                    os.exit(1)

                if isinstance(tile_def_in["id"], list):
                    self.id = tile_def_in["id"]
                else:
                    self.id = [tile_def_in["id"]]

                if "fg" in tile_def_in:
                    if isinstance(tile_def_in["fg"], list):
                        self.fg = map(Image.open, os.path.join(path, tile_def_in["fg"]))
                    else:
                        self.fg = [Image.open(os.path.join(path, tile_def_in["fg"]))]

                if "bg" in tile_def_in:
                    if isinstance(tile_def_in["bg"], list):
                        self.bg = map(Image.open, os.path.join(path, tile_def_in["bg"]))
                    else:
                        self.bg = [Image.open(os.path.join(path, tile_def_in["bg"]))]

                if "autotile" in tile_def_in and tile_def_in["autotile"]:
                    if "autotile_fg" not in tile_def_in and "autotile_bg" not in tile_def_in:
                        print("Error reading {0}: need at least one of autotile_fg or autotile_bg".format(
                            os.path.join(path, json_or_none)))
                        os.exit(1)
                    self.multitile = True
                    self.rotates = True
                    if "autotile_fg" in tile_def_in:
                        self.autotile_fg = Image.open(os.path.join(path, tile_def_in["autotile_fg"]))
                    if "autotile_bg" in tile_def_in:
                        self.autotile_bg = Image.open(os.path.join(path, tile_def_in["autotile_bg"]))


def main():
    args = parser.parse_args()
    out = {}
    out_dir = os.getcwd()
    for root, dirs, files in os.walk(args.path):

        if "tileset.txt" not in files:
            print("Couldn't find tileset.txt")
            os.exit(1)
        else:
            with open(os.path.join(root, "tileset.txt"), "r") as fp:
                lines = fp.readlines()

                name_line_or_none = next((line for line in lines if line.startswith("NAME: ")), None).strip()
                if not name_line_or_none:
                    print("Error reading tileset.txt: Missing 'NAME:' statement")
                    os.exit(1)
                else:
                    out_dir = os.path.join(out_dir, name_line_or_none.split(" ")[1])
                    os.makedirs(out_dir, exist_ok=True)

                view_line_or_none = next((line for line in lines if line.startswith("VIEW: ")), None).strip()
                if not view_line_or_none:
                    print("Error reading tileset.txt: Missing 'VIEW:' statement")
                    os.exit(1)

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
            print("Couldn't find tile_info.json")
            os.exit(1)
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

        for directory in dirs:
            print("Processing {0}".format(os.path.join(root, directory)))
            current_file = {"file": directory + ".png"}
            tile_defs = []
            sprite_width = tile_width
            sprite_height = tile_height
            for root2, dirs2, files2 in os.walk(os.path.join(root, directory)):
                if directory + ".json" in files2:
                    with open(os.path.join(root2, directory + ".json"), "r") as fp:
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
                for subdirectory in dirs2:
                    tile_defs.append(Tile_Def(os.path.join(root2, subdirectory)))

                break  # os.walk
            tiles = []
            sprites = []
            for tile_def in tile_defs:
                tile = {}
                tile["id"] = tile_def.id

                if tile_def.fg:
                    if len(tile_def.fg) == 1:
                        tile["fg"] = len(sprites)
                        sprites.append(tile_def.fg[0])
                    else:
                        tile["fg"] = []
                        for sprite in tile_def.fg:
                            tile["fg"].append(len(sprites))
                            sprites.append(sprite)

                if tile_def.bg:
                    if len(tile_def.bg) == 1:
                        tile["bg"] = len(sprites)
                        sprites.append(tile_def.bg[0])
                    else:
                        tile["bg"] = []
                        for sprite in tile_def.bg:
                            tile["bg"].append(len(sprites))
                            sprites.append(sprite)

                if tile_def.autotile_fg is not None or tile_def.autotile_bg is not None:
                    tile["multitile"] = True,
                    tile["rotates"] = True,
                    tile["addtional_tiles"] = autotile_to_tile_config(sprites, tile_def.autotile_fg,
                                                                      tile_def.autotile_bg, tile_width, tile_height)

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
