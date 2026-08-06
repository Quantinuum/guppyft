//! CLI for generating JSON from extensions defined in rust.

use anyhow::Result;
use clap::Parser as _;
use extensions::cli::CliArgs;

fn main() -> Result<()> {
    match CliArgs::parse() {
        CliArgs::GenExtensions(args) => {
            let reg = extensions::all_extensions();

            args.run_dump(&reg)?;
        }
        _ => {
            eprintln!("Unknown command");
            std::process::exit(1);
        }
    };

    Ok(())
}
