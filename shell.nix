{ pkgs ? import <nixpkgs> { } }:

let
  python = pkgs.python3.withPackages (ps: builtins.attrValues {
    inherit (ps) python-docx python-lsp-server;
  });
in python.env
