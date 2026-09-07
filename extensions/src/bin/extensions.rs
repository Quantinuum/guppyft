//! CLI for generating JSON from extensions defined in rust.

use anyhow::Result;
use clap::Parser as _;
use extensions::cli::CliArgs;
use hugr::extension::ExtensionRegistry;

fn main() -> Result<()> {
    match CliArgs::parse() {
        CliArgs::GenExtensions(args) => {
            let reg = ExtensionRegistry::new([
                extensions::std::types::EXTENSION.to_owned(),
                extensions::std::ops::EXTENSION.to_owned(),
                extensions::iceberg::types::EXTENSION.to_owned(),
                extensions::iceberg::ops::EXTENSION.to_owned(),
                extensions::steane::types::EXTENSION.to_owned(),
                extensions::steane::ops::EXTENSION.to_owned(),
                extensions::toy_k2::types::EXTENSION.to_owned(),
                extensions::toy_k2::ops::EXTENSION.to_owned(),
            ]);

            args.run_dump(&reg)?;
        }
        _ => {
            eprintln!("Unknown command");
            std::process::exit(1);
        }
    };

    Ok(())
}
