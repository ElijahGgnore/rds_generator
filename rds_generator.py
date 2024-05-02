import argparse
from random import choice

from PIL import Image
import numpy as np

DEFAULT_X_DPI = 75.0
DEFAULT_EYE_SEPARATION_FACTOR = 0.7
DEFAULT_EYE_SEPARATION_INCHES = 2.5
DEFAULT_OBSERVER_DISTANCE_INCHES = 12.0


def andrew_steer_rds(_img: Image, x_dpi: float = DEFAULT_X_DPI,
                     separation_factor: float = DEFAULT_EYE_SEPARATION_FACTOR,
                     eye_separation_inches: float = DEFAULT_EYE_SEPARATION_INCHES,
                     observer_distance_inches: float = DEFAULT_OBSERVER_DISTANCE_INCHES):
    observer_distance = x_dpi * observer_distance_inches
    eye_separation = x_dpi * eye_separation_inches
    max_depth = observer_distance
    min_depth = (separation_factor * max_depth * observer_distance) / (
            (1 - separation_factor) * max_depth + observer_distance)

    width = _img.width
    height = _img.height
    depth_map_array = np.asarray(_img)

    autostereogram_array = np.zeros((width, height, 3), np.int8)
    for y, row in enumerate(depth_map_array):
        links_left = np.array([x for x in range(width)])
        links_right = np.array([x for x in range(width)])
        for x, depth in enumerate(row):
            feature_z = max_depth - (depth / 256) * (max_depth - min_depth)
            stereo_separation = int(eye_separation * (feature_z / (observer_distance + feature_z)))
            x_left = x - stereo_separation // 2
            x_right = x_left + stereo_separation

            # Create links and remove hidden-surfaces
            visible = True
            if x_left >= 0 and x_right < width:
                if links_left[x_right] != x_right:  # Right point already linked.
                    if links_left[x_right] < x_left:  # Deeper than the current.
                        links_right[links_left[x_right]] = links_left[x_right]  # break old links
                        links_left[x_right] = x_right
                    else:
                        visible = False

                if links_right[x_left] != x_left:  # Left point already linked
                    if links_right[x_left] > x_right:  # Deeper than current
                        links_left[links_right[x_left]] = links_right[x_left]  # break old links
                        links_right[x_left] = x_left
                    else:
                        visible = False

                if visible:
                    # Make links
                    links_left[x_right] = x_left
                    links_right[x_left] = x_right
        for x_right, x_left in enumerate(links_left):
            if x_left == x_right:
                autostereogram_array[y, x_right] = choice((0, 255))
            else:
                autostereogram_array[y, x_right] = autostereogram_array[y, x_left]
    return Image.fromarray(autostereogram_array, 'RGB')


def main():
    # Parse the command-line arguments
    parser = argparse.ArgumentParser()

    parser.add_argument('source',
                        help='Path to the depth map used to generate an auto stereogram.')
    parser.add_argument('-d', '--xdpi',
                        help='Horizontal dpi value used in the depth calculation.',
                        default=DEFAULT_X_DPI,
                        type=float)
    parser.add_argument('-o', '--observer-distance',
                        help='The distance between the observer and the screen in inches.',
                        default=DEFAULT_OBSERVER_DISTANCE_INCHES,
                        type=float)
    parser.add_argument('-e', '--eye-separation',
                        help='The distance between the observer\'s eyes in inches.',
                        default=DEFAULT_EYE_SEPARATION_INCHES,
                        type=float)
    parser.add_argument('-s', '--stereo-separation-factor',
                        help='The stereo separation factor used in the depth calculation.',
                        default=DEFAULT_EYE_SEPARATION_FACTOR,
                        type=float)
    parser.add_argument('-f', '--output-file', help='The file to save the resulting image to.')

    args = parser.parse_args()

    # Load the specified depth map
    img = Image.open(args.source).convert('L')
    resulting_image_path = ''
    if args.output_file:
        resulting_image_path = args.output_file
    else:  # Use the source name with a suffix if the resulting file was not passed
        dot_index = args.source.rfind('.')
        resulting_image_path = args.source[:dot_index] \
                               + f'-autostereogram-xdpi_{args.xdpi}-od_{args.observer_distance}-es_{args.eye_separation}-esf_{args.stereo_separation_factor}' \
                               + args.source[dot_index:]
    andrew_steer_rds(img, args.xdpi, args.stereo_separation_factor, args.eye_separation,
                     args.observer_distance).save(resulting_image_path)


if __name__ == '__main__':
    main()
