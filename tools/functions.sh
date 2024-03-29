function maybe_compile() {
    file="$1"
    target="$2"
    if [[ $CCLOCK_SIMULATOR_MODE ]]; then
        cp "$file" "$target"
    else
        name=$(basename "$file")
        env/bin/mpy-cross -o "$target"/${name%.py}.mpy -s "$name" "$file"
    fi
}

function build() {
    source="$1"
    target="$2"

    # Let the tools/preprocess script do whatever it wants to the code; it's
    # a separate script because we want functions.sh to stay stable.
    prep_dir=/tmp/prep.$$
    mkdir -p $prep_dir
    cp "$source"/*.mcf "$source"/*.py $prep_dir
    tools/preprocess $prep_dir

    rm -rf "$target"
    mkdir -p "$target"
    cp $prep_dir/*.mcf "$target"
    for file in $prep_dir/*.py; do
        name=$(basename $file)
        [[ $name = boot.py || $name = main.py ]] && continue
        maybe_compile $file "$target"
    done

    [[ $CCLOCK_KEEP_TEMP_FILES ]] || rm -rf $prep_dir
}
