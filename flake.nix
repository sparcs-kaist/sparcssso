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
            pkgs.mysql84
          ];

          shellHook = ''
            # Create .envrc if it doesn't exist
            if [ ! -f .envrc ]; then
              echo "Creating .envrc file..."
              cat > .envrc << EOF
            # This file was generated by the Nix flake
            if [ -d ./.venv ]; then
              source ./.venv/bin/activate
            fi
            EOF
              
              # Make direnv load the .envrc file if direnv is installed
              if command -v direnv >/dev/null 2>&1; then
                direnv allow
              fi
            fi

            # Run the setup script
            setup-venv

            # Activate the venv
            if [ -d ./.venv ]; then
              source ./.venv/bin/activate
              export PYTHONPATH="$PWD:$PYTHONPATH"
              echo "Virtual environment activated. Run 'deactivate' to exit."
              echo "Use 'pip install <package>' to install additional packages."
            fi

            echo "Python version: $(python --version)"
            echo "Pip version: $(pip --version)"
          '';
        };
      }
    );
}