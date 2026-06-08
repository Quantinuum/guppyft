{ pkgs, lib, config, inputs, ... }: let
  hugrenv-unwrapped = pkgs.callPackage ./hugrenv.nix {
    packages = ["tket" "llvm"];
  };
  hugrenv = pkgs.stdenv.mkDerivation {
    name = "hugrenv-wrapped";
    nativeBuildInputs = [ pkgs.autoPatchelfHook ];
    buildInputs = [ pkgs.stdenv.cc.cc.lib pkgs.gfortran.cc.lib ];
    src = hugrenv-unwrapped;
    installPhase = ''
        mkdir -p $out
        cp -rL $src/* $out/
        chmod +w -R $out/*
        rm $out/lib64/cmake -fr
    '';
    };
in {

  env = {
    "LLVM_SYS_211_PREFIX" = "${hugrenv}";
    "TKET_C_API_PATH" = "${hugrenv}";
  };

  enterShell = ''
      export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  '';

  packages = [
    pkgs.libffi
    pkgs.just
    pkgs.cargo-insta
    pkgs.cargo-nextest
  ];

  languages.python = {
    enable = true;
    uv.enable = true;
    venv.enable = true;
    lsp = {
        enable = true;
      package = pkgs.ty;
    };
  };

  languages.rust = {
    enable = true;
  };
}
