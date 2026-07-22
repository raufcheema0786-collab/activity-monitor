function ScreenshotGallery({ screenshots }) {
  const openScreenshot = (path) => {
    window.pywebview.api.open_screenshot(path);
  };

  return (
    <div style={{ textAlign: "left", maxWidth: "500px", margin: "20px auto" }}>
      <h3>Screenshots</h3>
      {screenshots.length === 0 && <p>No screenshots captured.</p>}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "16px" }}>
        {screenshots.map((shot) => (
          <div
            key={shot.id}
            style={{
              width: "120px",
              textAlign: "center",
              cursor: "pointer",
            }}
            onClick={() => openScreenshot(shot.path)}
          >
            <img
              src={shot.path}
              alt={`Screenshot ${shot.id}`}
              style={{ width: "120px", height: "auto", display: "block", marginBottom: "8px" }}
            />
            <div style={{ fontSize: "0.9rem" }}>
              {new Date(shot.captured_at).toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ScreenshotGallery;
