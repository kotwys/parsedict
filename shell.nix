{ pkgs ? import <nixpkgs> { } }:

let
  python = pkgs.python3.withPackages (ps: builtins.attrValues {
    inherit (ps) python-lsp-server virtualenv;
  });
in python.env
