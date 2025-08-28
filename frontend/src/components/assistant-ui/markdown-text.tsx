import { ComponentPropsWithoutRef, forwardRef } from "react";

interface MarkdownTextProps extends ComponentPropsWithoutRef<"div"> {
  content?: string;
}

const MarkdownText = forwardRef<HTMLDivElement, MarkdownTextProps>(
  ({ content, children, className, ...props }, ref) => {
    return (
      <div 
        {...props} 
        ref={ref} 
        className={`prose prose-sm max-w-none ${className || ''}`}
      >
        {content || children}
      </div>
    );
  }
);

MarkdownText.displayName = "MarkdownText";

export { MarkdownText };