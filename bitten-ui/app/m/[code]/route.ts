import { NextRequest, NextResponse } from "next/server";

export async function GET(
  request: NextRequest,
  { params }: { params: { code: string } },
) {
  const code = params.code;

  // Proxy to Flask backend directly (NOT through NGINX)
  const backendUrl = "http://localhost:8888";

  try {
    const response = await fetch(`${backendUrl}/m/${code}`, {
      redirect: "manual", // Don't follow redirects automatically
    });

    // Flask returns 302 redirect to /mission?ms=...&token=...
    if (response.status === 302 || response.status === 301) {
      const location = response.headers.get("Location");
      if (location) {
        // Use the request's host to build proper redirect URL
        if (location.startsWith("/")) {
          // Get the actual host from the request headers (preserves production domain)
          const host = request.headers.get("host") || "joinbitten.com";
          const protocol = request.headers.get("x-forwarded-proto") || "https";
          const redirectUrl = `${protocol}://${host}${location}`;

          console.log(`[/m/${code}] Redirecting to: ${redirectUrl}`);
          return NextResponse.redirect(redirectUrl);
        } else {
          // Absolute URL (shouldn't happen but handle it)
          console.log(`[/m/${code}] Redirecting to: ${location}`);
          return NextResponse.redirect(location);
        }
      }
    }

    // Handle errors from backend
    if (!response.ok) {
      try {
        const error = await response.json();
        return NextResponse.json(error, { status: response.status });
      } catch {
        return NextResponse.json(
          { error: "Backend error", status: response.status },
          { status: response.status },
        );
      }
    }

    // Fallback
    return NextResponse.json(
      { error: "Invalid response from server" },
      { status: 500 },
    );
  } catch (error) {
    console.error("Short code resolution error:", error);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
