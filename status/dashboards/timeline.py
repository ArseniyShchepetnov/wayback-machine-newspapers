import plotly.graph_objects as go


def plot_datetime_title(data, width=800, height=400):

    fig = go.Figure()

    data = data.sort_values(by=['datetime'])
    data = data.reset_index(drop=True)

    fig.add_trace(go.Scatter(
        x=data['datetime'],
        y=-2*data.index,
        mode="lines+markers+text",
        name="News",
        text=data['title'],
        textposition="top right"
    ))

    fig.update_layout(
        autosize=True,
        width=width,
        height=height,

    )

    return fig
