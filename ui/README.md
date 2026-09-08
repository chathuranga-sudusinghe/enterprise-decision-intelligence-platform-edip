This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Production deployment direction

AWS is the canonical production target. The frontend will be packaged as an OCI image, published to Amazon ECR, and released to its Amazon ECS Fargate service through the approved GitHub Actions CD workflow using AWS OpenID Connect (OIDC). Application Load Balancer routing and `NEXT_PUBLIC_API_BASE_URL` behavior must be defined by the AWS deployment ADR before implementation. No production frontend image or deployment workflow exists yet.

See the [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for framework-level runtime guidance.
