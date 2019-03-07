#!/usr/bin/env python3

"""
Tileset Compiler for Cataclysm Dark Days Ahead
"""

import os
import argparse
import json
from PIL import Image

parser = argparse.ArgumentParser( description="Compile a tileset for Cataclysm Dark Days Ahead" )
parser.add_argument( "path", help="path to the tileset" )

# Loads and stores the tile definiton from path
class Tile_Def:
    id = []
    fg = []
    bg = []
    multitile = False
    rotates = False
    additional_tiles = []

    def __init__( self, path ):
        contents = os.listdir( path )
        json_or_none = next( ( f for f in contents if f.endswith( ".json" ) ), None )
        if not json_or_none:
            print( "Error: missing json file in {0}".format( path ) )
            os.exit( 1 )
        else:
            with open( os.path.join( path, json_or_none ), "r" ) as fp:
                tile_def_in = json.load( fp )

                if not "id" in tile_def_in:
                    print( "Error reading {0}: missing id".format( os.path.join( path, json_or_none ) ) )
                    os.exit( 1 )
                if not ( "fg" in tile_def_in or "bg" in tile_def_in ):
                    print( "Error reading {0}: need at least one of fg or bg".format( os.path.join( path, json_or_none ) ) )
                    os.exit( 1 )

                if isinstance( tile_def_in[ "id" ], list ):
                    self.id = tile_def_in[ "id" ]
                else:
                    self.id = [ tile_def_in[ "id" ] ]

                if "fg" in tile_def_in:
                    if isinstance( tile_def_in[ "fg" ], list ):
                        self.fg = map( Image.open, os.path.join( path, tile_def_in[ "fg" ] ) )
                    else:
                        self.fg = [ Image.open( os.path.join( path, tile_def_in[ "fg" ] ) ) ]

                if "bg" in tile_def_in:
                    if isinstance( tile_def_in[ "bg" ], list ):
                        self.bg = map( Image.open, os.path.join( path, tile_def_in[ "bg" ] ) )
                    else:
                        self.bg = [ Image.open( os.path.join( path, tile_def_in[ "bg" ] ) ) ]

                if "rotates" in tile_def_in:
                    self.rotates = tile_def_in[ "rotates" ]
                if "multitile" in tile_def_in:
                    self.multitile = tile_def_in[ "multitile" ]
                if "additional_tiles" in tile_def_in:
                    self.additional_tiles = [] # Not supported

def main():
    args = parser.parse_args()
    out = {}
    out_dir = os.getcwd()
    for root, dirs, files in os.walk( args.path ):

        if not "tileset.txt" in files:
            print( "Couldn't find tileset.txt" )
            os.exit(1)
        else:
            with open( os.path.join( root, "tileset.txt" ), "r" ) as fp:
                lines = fp.readlines()

                name_line_or_none = next( ( line for line in lines if line.startswith( "NAME: " ) ), None ).strip()
                if not name_line_or_none:
                    print( "Error reading tileset.txt: Missing 'NAME:' statement" )
                    os.exit(1)
                else:
                    out_dir = os.path.join( out_dir, name_line_or_none.split( " " )[1] )
                    os.makedirs( out_dir, exist_ok=True )

                view_line_or_none = next( ( line for line in lines if line.startswith( "VIEW: " ) ), None ).strip()
                if not view_line_or_none:
                    print( "Error reading tileset.txt: Missing 'VIEW:' statement" )
                    os.exit(1)

                with open( os.path.join( out_dir, "tileset.txt" ), "w" ) as tileset_txt:
                    tileset_txt.write( "#Name of tileset\n" )
                    tileset_txt.write( name_line_or_none + "\n" )
                    tileset_txt.write( "\n" )
                    tileset_txt.write( "#Viewing (Option) name of the tileset\n" )
                    tileset_txt.write( view_line_or_none + "\n"  )
                    tileset_txt.write( "\n" )
                    tileset_txt.write( "#JSON Path - Default of tile_config.json\n" )
                    tileset_txt.write( "JSON: tile_config.json\n" )
                    tileset_txt.write( "\n" )
                    tileset_txt.write( "#Tileset Path - Default of tinytile.png\n" )
                    tileset_txt.write( "TILESET: tiles.png\n" )

        tile_height = 0
        tile_width = 0
        if not "tile_info.json" in files:
            print( "Couldn't find tile_info.json" )
            os.exit(1)
        else:
            with open( os.path.join( root, "tile_info.json" ), "r" ) as fp:
                tile_info = json.load( fp )

                out[ "tile_info" ] = []
                out[ "tile_info" ].append( {} )
                tile_height = tile_info[ "height" ]
                tile_width = tile_info[ "width" ]
                out[ "tile_info" ][0][ "height" ] = tile_height
                out[ "tile_info" ][0][ "width" ] = tile_width
                if "iso" in tile_info:
                    out[ "tile_info" ][0][ "iso" ] = tile_info[ "iso" ]
                if "pixelscale" in tile_info:
                    out[ "tile_info" ][0][ "pixelscale" ] = tile_info[ "pixelscale" ]

        out[ "tiles-new" ] = []
        
        for directory in dirs:
            print( "Processing {0}".format( os.path.join( root, directory ) ) )
            current_file = { "file": directory + ".png" }
            tile_defs = []
            sprite_width = tile_width
            sprite_height = tile_height
            for root2, dirs2, files2 in os.walk( os.path.join( root, directory ) ):
                if directory + ".json" in files2:
                    with open( os.path.join( root2, directory + ".json" ), "r" ) as fp:
                        tile_info = json.load( fp )

                        if "file" in tile_info and tile_info[ "file" ].endswith( ".png" ):
                            current_file[ "file" ] = tile_info[ "file" ]
                        if "sprite_width" in tile_info:
                            sprite_width = tile_info[ "sprite_width" ]
                            current_file[ "sprite_width" ] = sprite_width
                        if "sprite_height" in tile_info:
                            sprite_height = tile_info[ "sprite_height" ]
                            current_file[ "sprite_height" ] = sprite_height
                        if "sprite_offset_x" in tile_info:
                            current_file[ "sprite_offset_x" ] = tile_info[ "sprite_offset_x" ]
                        if "sprite_offset_y" in tile_info:
                            current_file[ "sprite_offset_y" ] = tile_info[ "sprite_offset_y" ]
                for subdirectory in dirs2:
                    tile_defs.append( Tile_Def( os.path.join( root2, subdirectory ) ) )

                break # os.walk
            tiles = []
            sprites = []
            sprite_index = 0
            for tile_def in tile_defs:
                tile = {}
                tile[ "id" ] = tile_def.id

                if tile_def.fg:
                    if len( tile_def.fg ) == 1:
                        sprites.append( tile_def.fg[0] )
                        tile[ "fg" ] = sprite_index
                        sprite_index += 1
                    else:
                        tile[ "fg" ] = []
                        for sprite in tile_def.fg:
                            sprites.append( sprite )
                            tile[ "fg" ].append( sprite_index )
                            sprite_index += 1

                if tile_def.bg:
                    if len( tile_def.bg ) == 1:
                        sprites.append( tile_def.bg[0] )
                        tile[ "bg" ] = sprite_index
                        sprite_index += 1
                    else:
                        tile[ "bg" ] = []
                        for sprite in tile_def.bg:
                            sprites.append( sprite )
                            tile[ "bg" ].append( sprite_index )
                            sprite_index += 1

                tile[ "multitile" ] = tile_def.multitile
                tile[ "rotates" ] = tile_def.rotates

                tiles.append( tile )

            current_file[ "tiles" ] = tiles
            out[ "tiles-new" ].append( current_file )

            atlas_width = 16 if len( sprites ) > 16 else len( sprites )
            atlas_height = len( sprites ) // 16 + 1

            # create transparent
            atlas = Image.new( "RGBA", ( atlas_width * sprite_width, atlas_height * sprite_height ), ( 255, 0, 0, 0 ) )

            i = 0
            for sprite in sprites:
                atlas.paste( sprite, ( i % atlas_width * sprite_width, i // atlas_width * sprite_height ) )
                i += 1

            atlas.save( os.path.join( out_dir, current_file[ "file" ] ), format="PNG" )

        break # os.walk

    # write output
    with open( os.path.join( out_dir, "tile_config.json" ), "w" ) as tile_config_json:
        json.dump( out, tile_config_json, indent=2 )




if __name__ == "__main__":
    main()
