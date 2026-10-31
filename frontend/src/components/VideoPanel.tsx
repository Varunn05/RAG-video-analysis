interface Props { videoId: string; startAt: number }
export function VideoPanel({ videoId, startAt }: Props) {
  return <section className="panel video-panel"><div className="panel-label">Source video</div><iframe title="YouTube video" src={`https://www.youtube.com/embed/${videoId}?start=${startAt}`} allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowFullScreen /></section>;
}
