"""LIME explanations section for interpretability page."""

import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st

from content.interpret.engine.data_loader import get_test_dataloader, get_test_samples
from content.interpret.engine.lime import compute_lime_explanation
from content.interpret.engine.model_loader import load_experiment_model
from content.interpret.tooltips import LIME_TOOLTIPS
from state.persistence import get_dataset_config_from_file
from state.workflow import get_session_id
from training.transforms import create_val_transforms


def render_lime_section(exp_id: str):
    """Render LIME explanations."""
    st.header("LIME Explanations", help=LIME_TOOLTIPS["method"])

    try:
        model, device, _ = load_experiment_model(exp_id)
        _, class_names = get_test_dataloader(batch_size=1)

        col1, col2 = st.columns(2)

        with col1:
            samples = get_test_samples(n_samples=20)
            sample_options = {
                f"{s['class_name']} (idx {s['index']})": s for s in samples
            }
            selected_sample_name = st.selectbox(
                "Select Sample",
                options=list(sample_options.keys()),
                key="lime_sample_select",
                help="Choose a test image to explain.",
            )
            selected_sample = sample_options[selected_sample_name]

        with col2:
            num_samples = st.slider(
                "Perturbation Samples", 50, 200, 100,
                key="lime_num_samples",
                help=LIME_TOOLTIPS["num_samples"],
            )
            num_features = st.slider(
                "Top Features", 5, 20, 10,
                key="lime_num_features",
                help=LIME_TOOLTIPS["num_features"],
            )

        if st.button("Compute LIME Explanation", key="lime_run"):
            with st.spinner("Computing LIME (this may take a moment)..."):
                try:
                    session_id = get_session_id()
                    dataset_config = get_dataset_config_from_file(session_id)
                    transform = create_val_transforms(dataset_config)

                    img = Image.open(selected_sample["path"]).convert("RGB")
                    img_tensor = transform(img)

                    explanation = compute_lime_explanation(
                        model,
                        device,
                        img_tensor,
                        class_names,
                        num_samples=num_samples,
                        num_features=num_features,
                    )

                    st.session_state["lime_explanation"] = explanation
                    st.session_state["lime_img"] = img
                    st.session_state["lime_true_class"] = selected_sample["class_name"]

                except ImportError:
                    st.error(
                        "LIME requires scikit-image. Install: pip install scikit-image"
                    )
                except Exception as e:
                    st.error(f"LIME failed: {e}")
                    import traceback
                    st.code(traceback.format_exc())

        _display_lime_results()

    except Exception as e:
        st.error(f"Failed: {e}")


def _display_lime_results():
    """Display LIME results from session state."""
    if "lime_explanation" not in st.session_state:
        return

    from skimage.segmentation import mark_boundaries

    explanation = st.session_state["lime_explanation"]
    orig_img = st.session_state["lime_img"]
    true_class = st.session_state["lime_true_class"]

    st.divider()

    st.caption(
        f"True: **{true_class}** | Predicted: **{explanation['pred_class_name']}** "
        f"({explanation['pred_prob'] * 100:.1f}%)"
    )
    st.caption(f"Segmented into {explanation['num_segments']} superpixels")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Original")
        st.image(orig_img.resize((224, 224)), width="stretch")

    with col2:
        st.subheader("Superpixels", help=LIME_TOOLTIPS["superpixels"])
        img_array = np.array(orig_img.resize((224, 224)))
        segments = explanation["segments"]
        seg_resized = np.array(
            Image.fromarray(segments.astype(np.uint8)).resize((224, 224), Image.NEAREST)
        )
        boundaries = mark_boundaries(img_array / 255.0, seg_resized)
        st.image(boundaries, width="stretch")

    with col3:
        st.subheader("Explanation", help="Green = supports prediction, Red = contradicts.")
        pos_mask = explanation["positive_mask"]
        neg_mask = explanation["negative_mask"]

        pos_resized = np.array(
            Image.fromarray((pos_mask * 255).astype(np.uint8)).resize((224, 224))
        ) / 255.0
        neg_resized = np.array(
            Image.fromarray((np.abs(neg_mask) * 255).astype(np.uint8)).resize((224, 224))
        ) / 255.0

        overlay = img_array.copy().astype(float) / 255.0
        overlay[:, :, 1] = np.clip(overlay[:, :, 1] + pos_resized * 0.5, 0, 1)
        overlay[:, :, 0] = np.clip(overlay[:, :, 0] + neg_resized * 0.5, 0, 1)

        st.image(overlay, width="stretch")

    with st.expander("Segment Importance Scores"):
        top_segments = explanation["top_segments"]
        importances = explanation["segment_importance"]

        data = [
            {"Segment": seg, "Importance": f"{importances[seg]:.4f}"}
            for seg in top_segments
        ]
        st.dataframe(pd.DataFrame(data), width="stretch", hide_index=True)
