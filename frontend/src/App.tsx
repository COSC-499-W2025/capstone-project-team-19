import { RouterProvider } from "react-router-dom";
import { useState } from "react";

import { createAppRouter } from "./router";

export default function App() {
  const [router] = useState(createAppRouter);
  return <RouterProvider router={router} />;
}
