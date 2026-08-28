from pathlib import Path
import shutil

from tqdm import tqdm


def merge_dataset():
    # Configuration
    repo_path = Path("repo")
    target_path = Path("dataset")

    # Source directories to merge
    source_dirs = ["training", "validation", "test"]

    print(f"Starting merge from {repo_path} to {target_path}...")

    # Create target directory if it doesn't exist
    if not target_path.exists():
        target_path.mkdir(parents=True)
        print(f"Created directory: {target_path}")

    total_copied = 0

    # Iterate through each source directory (training, validation, test)
    for source_name in source_dirs:
        source_dir = repo_path / source_name

        if not source_dir.exists():
            print(f"Skipping {source_name} (not found)")
            continue

        print(f"Processing {source_name}...")

        # Iterate through each class (family) directory
        for class_dir in source_dir.iterdir():
            if not class_dir.is_dir() or class_dir.name.startswith("."):
                continue

            class_name = class_dir.name
            target_class_dir = target_path / class_name

            # Create class directory in target if it doesn't exist
            if not target_class_dir.exists():
                target_class_dir.mkdir(exist_ok=True)

            # Copy images
            files = list(
                class_dir.glob("*.png")
            )  # Assuming .png, add other extensions if needed
            for file_path in tqdm(
                files, desc=f"Copying {class_name} from {source_name}", leave=False
            ):
                dest_file = target_class_dir / file_path.name

                # Handle potential duplicate filenames (though unlikely with hashes)
                if dest_file.exists():
                    print(
                        f"Warning: File {file_path.name} already exists in {class_name}. Skipping."
                    )
                    continue

                shutil.copy2(file_path, dest_file)
                total_copied += 1

    print(f"\nMerge complete! {total_copied} files copied to {target_path}")
    print(
        "You can now delete the 'repo' folder if you want to save space, or keep it as backup."
    )


if __name__ == "__main__":
    exit(merge_dataset())
