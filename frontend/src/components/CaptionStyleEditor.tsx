import { useState } from "react";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Play } from "lucide-react";

export interface CaptionStyle {
  fontFamily: string;
  fontSize: number;
  textColor: string;
  strokeColor: string;
}

interface CaptionStyleEditorProps {
  style: CaptionStyle;
  onChange: (style: CaptionStyle) => void;
}

const COLOR_OPTIONS = [
  { value: "white", label: "White", color: "#FFFFFF" },
  { value: "yellow", label: "Yellow", color: "#FFFF00" },
  { value: "green", label: "Green", color: "#00FF00" },
];

const FONT_FAMILIES = [
  { value: "Arial", label: "Arial" },
  { value: "Inter", label: "Inter" },
  { value: "Impact", label: "Impact" },
  { value: "Montserrat", label: "Montserrat" },
];

export const CaptionStyleEditor = ({ style, onChange }: CaptionStyleEditorProps) => {
  const [localStyle, setLocalStyle] = useState<CaptionStyle>(style);

  const updateStyle = (updates: Partial<CaptionStyle>) => {
    const newStyle = { ...localStyle, ...updates };
    setLocalStyle(newStyle);
    onChange(newStyle);
  };

  return (
    <div className="flex gap-6 w-full">
      {/* Left Panel - Controls */}
      <div className="flex flex-col gap-6 w-64">
        {/* Colors */}
        <div className="space-y-2">
          <Label>Colors</Label>
          <Select
            value={localStyle.textColor}
            onValueChange={(value) => updateStyle({ textColor: value })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {COLOR_OPTIONS.map((color) => (
                <SelectItem key={color.value} value={color.value}>
                  <div className="flex items-center gap-2">
                    <div
                      className="w-4 h-4 rounded-full border border-border"
                      style={{ backgroundColor: color.color }}
                    />
                    {color.label}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Font Size Slider */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>Font</Label>
            <span className="text-sm text-muted-foreground">{localStyle.fontSize}</span>
          </div>
          <Slider
            value={[localStyle.fontSize]}
            onValueChange={([value]) => updateStyle({ fontSize: value })}
            min={12}
            max={64}
            step={1}
            className="w-full"
          />
        </div>

        {/* Font Family (Optional) */}
        <div className="space-y-2">
          <Label>Font Family</Label>
          <Select
            value={localStyle.fontFamily}
            onValueChange={(value) => updateStyle({ fontFamily: value })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {FONT_FAMILIES.map((font) => (
                <SelectItem key={font.value} value={font.value}>
                  {font.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Middle - Preview Pane */}
      <div className="flex-1 flex items-center justify-center">
        <div className="relative w-full max-w-[270px] aspect-[9/16] bg-black rounded-lg overflow-hidden border-2 border-border">
          {/* Phone mockup frame */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            {/* Play button overlay */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-16 h-16 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center border-2 border-white/30">
                <Play className="h-8 w-8 text-white ml-1" fill="white" />
              </div>
            </div>

            {/* Caption preview overlay (bottom) */}
            <div className="absolute bottom-8 left-4 right-4">
              <div
                className="text-center px-4 py-2 rounded"
                style={{
                  fontFamily: localStyle.fontFamily,
                  fontSize: `${localStyle.fontSize * 0.6}px`, // Scale down for preview
                  color: COLOR_OPTIONS.find((c) => c.value === localStyle.textColor)?.color || "#FFFF00",
                  textShadow: `2px 2px 4px rgba(0,0,0,0.8), -1px -1px 2px rgba(0,0,0,0.8)`,
                  WebkitTextStroke: `1px ${localStyle.strokeColor === "black" ? "#000000" : "#FFFFFF"}`,
                  WebkitTextFillColor: COLOR_OPTIONS.find((c) => c.value === localStyle.textColor)?.color || "#FFFF00",
                }}
              >
                Sample Caption Text
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

