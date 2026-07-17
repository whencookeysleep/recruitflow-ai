export function LoadingBlock() {
  return <div className="rounded-md border border-line bg-white p-6 text-sm text-muted">加载中...</div>;
}

export function ErrorBlock({ message }: { message: string }) {
  return <div className="rounded-md border border-red-200 bg-red-50 p-6 text-sm text-danger">加载失败：{message}</div>;
}

export function EmptyBlock({ message }: { message: string }) {
  return <div className="rounded-md border border-line bg-white p-6 text-sm text-muted">{message}</div>;
}
