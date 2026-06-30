import OriginalRoot from "@theme-original/Root";
import SiteNav from "../components/SiteNav";

export default function Root({ children }) {
  return (
    <OriginalRoot>
      <SiteNav />
      {children}
    </OriginalRoot>
  );
}
