# Streamlit API Reference (Agent-Readable)

## 1. Display & Output

### Write & Magic
- `st.write(*args)` - Universal output function
- `st.write_stream(stream)` - Typewriter effect for generators/LLM streams
- Magic: Variables on own line auto-display

### Text
- `st.title(text)`, `st.header(text)`, `st.subheader(text)` - Headings
- `st.markdown(text)` - Markdown formatting
- `st.code(code, language)` - Syntax-highlighted code blocks
- `st.latex(formula)` - LaTeX math expressions
- `st.caption(text)` - Small text
- `st.badge(text)` - Colored badge
- `st.text(text)` - Preformatted text
- `st.divider()` - Horizontal rule
- `st.html(html_string)` - Render HTML

### Data Display
- `st.dataframe(df)` - Interactive table
- `st.data_editor(df, num_rows="dynamic")` - Editable data widget
- `st.table(df)` - Static table
- `st.metric(label, value, delta)` - Large metric with change indicator
- `st.json(dict_or_json)` - Pretty JSON
- `st.column_config.NumberColumn()`, `.TextColumn()`, etc. - Column configs

### Charts
**Simple:**
- `st.area_chart(df)`, `st.bar_chart(df)`, `st.line_chart(df)`, `st.scatter_chart(df)`
- `st.map(df)` - Scatterplot map

**Advanced:**
- `st.pyplot(fig)` - Matplotlib
- `st.plotly_chart(fig)` - Plotly
- `st.altair_chart(chart)` - Altair
- `st.bokeh_chart(fig)` - Bokeh
- `st.pydeck_chart(spec)` - PyDeck
- `st.graphviz_chart(spec)` - GraphViz

### Media
- `st.image(src)` - Image display
- `st.audio(src)` - Audio player
- `st.video(src)` - Video player
- `st.pdf(file)` - PDF viewer
- `st.logo(image)` - App logo

## 2. Input Widgets

### Selection
- `st.selectbox(label, options)` - Dropdown
- `st.multiselect(label, options)` - Multi-select
- `st.radio(label, options)` - Radio buttons
- `st.checkbox(label)` - Checkbox
- `st.pills(label, options)` - Pill buttons
- `st.segmented_control(label, options)` - Segmented control
- `st.toggle(label)` - Toggle switch

### Text Input
- `st.text_input(label)` - Single-line text
- `st.text_area(label)` - Multi-line text
- `st.chat_input(placeholder)` - Chat input

### Numeric Input
- `st.number_input(label, min_value, max_value)` - Number input
- `st.slider(label, min_value, max_value)` - Slider
- `st.select_slider(label, options)` - Discrete slider

### Date/Time
- `st.date_input(label)` - Date picker
- `st.time_input(label)` - Time picker

### File & Media
- `st.file_uploader(label, type)` - File upload
- `st.camera_input(label)` - Camera capture
- `st.audio_input(label)` - Audio recording

### Other
- `st.color_picker(label)` - Color picker
- `st.feedback(type)` - Rating/sentiment buttons

### Buttons
- `st.button(label)` - Action button
- `st.download_button(label, data, file_name)` - Download trigger
- `st.link_button(label, url)` - External link
- `st.page_link(page, label)` - Internal page link
- `st.form_submit_button(label)` - Form submit (use with `st.form`)

## 3. Layout & Containers

- `st.columns(n)` - Returns n column objects
- `st.container()` - Multi-element container
- `st.empty()` - Single replaceable placeholder
- `st.expander(label)` - Collapsible section
- `st.popover(label)` - Pop-up container
- `st.sidebar.element()` - Sidebar placement
- `st.tabs([labels])` - Tab interface
- `st.space(size)` - Vertical/horizontal spacing
- `@st.dialog(title)` - Modal dialog decorator

## 4. Chat Interface

- `st.chat_message(name)` - Chat message container
- `st.chat_input(placeholder)` - Chat input widget
- `st.write_stream(stream)` - Stream text with typewriter effect

## 5. Status & Feedback

### Progress
- `st.progress(value)` - Progress bar (0-100)
- `st.spinner(text)` - Loading spinner context
- `st.status(label)` - Task status container

### Notifications
- `st.toast(message, icon)` - Temporary toast notification
- `st.success(message)` - Success alert
- `st.info(message)` - Info alert
- `st.warning(message)` - Warning alert
- `st.error(message)` - Error alert
- `st.exception(exception)` - Exception display

### Celebrations
- `st.balloons()` - Balloon animation
- `st.snow()` - Snow animation

## 6. App Logic & Control

### Execution
- `st.rerun()` - Trigger immediate rerun
- `st.stop()` - Stop execution
- `@st.fragment(run_every)` - Independent rerun fragment
- `st.form(key)` - Batch inputs with submit button

### State Management
- `st.session_state[key] = value` - Per-user session state
- `st.query_params[key] = value` - URL query parameters
- `st.query_params.clear()` - Clear query params
- `st.context.cookies`, `st.context.headers` - Browser context

### Caching
- `@st.cache_data` - Cache data/transformations
- `@st.cache_resource` - Cache global resources (DB connections, models)

## 7. Navigation & Pages

- `st.navigation(pages_dict)` - Configure multipage app
- `st.Page(path, title, icon)` - Define page
- `st.switch_page(page)` - Navigate programmatically
- `st.page_link(page, label, icon)` - Link to page

## 8. Data Connections

- `st.connection(name, type)` - Create data connection
- `st.connection('sql')` - SQL database (SQLAlchemy)
- `st.connection('snowflake')` - Snowflake
- `st.secrets[key]` - Access secrets from `.streamlit/secrets.toml`
- `BaseConnection` - Custom connection base class

## 9. Authentication

- `st.login()` - Start auth flow
- `st.logout()` - Remove user identity
- `st.user.is_logged_in` - Check login status
- `st.user.name`, `st.user.email` - User info

## 10. Configuration

- `st.set_page_config(page_title, page_icon, layout, initial_sidebar_state)` - Page settings
- `st.set_option(key, value)` - Set config option
- `st.get_option(key)` - Get config option
- `.streamlit/config.toml` - Configuration file

## 11. Testing (st.testing.v1)

- `AppTest.from_file(path)` - Load app from file
- `AppTest.from_string(code)` - Load app from string
- `AppTest.from_function(callable)` - Load app from function
- `at.run()` - Run the app
- `at.button[0].click().run()` - Interact with widgets
- `at.text_input[0].input("text").run()` - Set input values
- Element classes: `Button`, `TextInput`, `Checkbox`, `Selectbox`, etc.

## 12. Custom Components

### V2 (Current)
- `st.components.v2.component(html, js)` - Register component
- `@streamlit/component-v2-lib` - npm package

### V1 (Legacy)
- `st.components.v1.declare_component(name, path)` - Declare component
- `st.components.v1.html(html_string)` - Render HTML
- `st.components.v1.iframe(url)` - Embed iframe

## Quick Patterns

**Form submission:**
```python
with st.form("my_form"):
    name = st.text_input("Name")
    if st.form_submit_button("Submit"):
        st.write(f"Hello {name}")
```

**Columns:**
```python
col1, col2 = st.columns(2)
col1.write("Column 1")
col2.write("Column 2")
```

**Session state:**
```python
if "counter" not in st.session_state:
    st.session_state.counter = 0
st.session_state.counter += 1
```

**Caching:**
```python
@st.cache_data
def load_data():
    return pd.read_csv("data.csv")
```

**Chat interface:**
```python
if prompt := st.chat_input("Say something"):
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        st.write("Response")
```
