{
  description = "Python development environment with venv";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ ];
        };

        pythonEnv = pkgs.python3;
        mysqlPkg = pkgs.mysql84;

        # Shell script to create and activate venv if it doesn't exist
        # and install packages from requirements.txt
        setupVenvScript = pkgs.writeShellScriptBin "setup-venv" ''
          if [ ! -d ./.venv ]; then
            echo "Creating new Python virtual environment..."
            ${pythonEnv}/bin/python -m venv ./.venv
          fi

          if [ -f ./requirements.txt ]; then
            echo "Installing packages from requirements.txt..."
            ./.venv/bin/pip install -r requirements.txt
          else
            echo "No requirements.txt found. Creating an empty one."
            touch requirements.txt
          fi

          echo "Python environment is ready!"
        '';

      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            setupVenvScript
          ] ++ (with pkgs; [
            mysqlPkg
            zlib
            zlib.dev
            libjpeg
            libtiff
            freetype
            lcms2
            libwebp
            tcl
            tk
            libffi
            pkg-config
            zstd 
          ]);

          NIX_CFLAGS_COMPILE = "-I${pkgs.zlib.dev}/include -I${pkgs.libjpeg.dev}/include -I${pkgs.zstd.dev}/include";
          
          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.zlib
            pkgs.libjpeg
            pkgs.libtiff
            pkgs.freetype
            pkgs.lcms2
            pkgs.libwebp
            pkgs.tcl
            pkgs.libffi
            pkgs.zstd
          ];
          
          # Add explicit linker flags for common libraries
          LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.zlib
            pkgs.zstd
          ];

          shellHook = ''
            # Run the setup script
            setup-venv

            # Activate the venv
            if [ -d ./.venv ]; then
              source ./.venv/bin/activate
              export PYTHONPATH="$PWD:$PYTHONPATH"
            fi

            alias django='python manage.py'
          '';
        };
      }
    );
}