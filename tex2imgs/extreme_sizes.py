import json
import os
import sys

import pandas as pd
import typer
from convert import read_tex


def remove_sizes(folder: str = "output"):
    # Open the sizes csv in the folder
    sizes = pd.read_csv(f"{folder}/sizes.csv")
    # Remove the 5 minimum and 5 maximum sizes
    sizes = sizes.nlargest(len(sizes) - 5, "Size")
    sizes = sizes.nsmallest(len(sizes) - 5, "Size")
    # Now take the list of files remaining
    files = sizes["Item"].tolist()
    # Remove those files from the folder
    for file in files:
        os.remove(f"{folder}/{file}.png")
    # Remove any other file that is not a png
    for file in os.listdir(folder):
        if not file.endswith(".png"):
            os.remove(f"{folder}/{file}")


def main(file: str = "examples/real.tex", config: str = "config.json"):
    dict_config = json.load(open(config))
    # Split the configuration into two: keys with dictionary values and keys with other values
    dict_subdicts = {
        key: value for key, value in dict_config.items() if isinstance(value, dict)
    }
    dict_params = {
        key: value for key, value in dict_config.items() if not isinstance(value, dict)
    }
    # Loop through the dictionaries
    for key, subdict in dict_subdicts.items():
        output = f"output_{key}"
        gen = read_tex(
            file,
            output,
            **dict_params,
            **subdict,
        )

        for p in gen:
            sys.stdout.write("\r%d%%" % (p * 100))
            sys.stdout.flush()

        remove_sizes(output)


if __name__ == "__main__":
    typer.run(main)
