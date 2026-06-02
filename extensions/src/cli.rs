//! CLI tools for extensions.

use clap::Parser;

/// CLI arguments.
#[derive(Parser, Debug)]
#[clap(version = "1.0", long_about = None)]
#[clap(about = "CLI tools for guppyft extensions")]
#[group(id = "extensions")]
#[non_exhaustive]
pub enum CliArgs {
    /// Generate serialized extensions.
    GenExtensions(hugr_cli::extensions::ExtArgs),
}
