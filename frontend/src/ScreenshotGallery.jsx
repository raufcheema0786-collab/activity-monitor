function ScreenshotGallery({ screenshots }) {
  const openScreenshot = (path) => {
    window.pywebview.api.open_screenshot(path);
  };

  if (screenshots.length === 0) return <p className="empty-state">No screenshots captured.</p>;

  return (
    <div className="gallery-grid">
      {screenshots.map((shot) => (
        <div key={shot.id} className="gallery-item" onClick={() => openScreenshot(shot.path)}>
          <img src={shot.path} alt={`Screenshot ${shot.id}`} />
          <div className="gallery-item-time">{new Date(shot.captured_at).toLocaleTimeString()}</div>
        </div>
      ))}
    </div>
  );
}

export default ScreenshotGallery;
