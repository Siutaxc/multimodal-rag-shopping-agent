import ProductDetailView from "./ProductDetailView";

export default async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ProductDetailView productId={id} />;
}
