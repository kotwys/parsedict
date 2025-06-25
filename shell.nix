{ pkgs ? import <nixpkgs> { } }:

let
  python = pkgs.python3.withPackages (ps: builtins.attrValues {
    inherit (ps) python-docx parsy regex python-lsp-server;
  });
in python.env
